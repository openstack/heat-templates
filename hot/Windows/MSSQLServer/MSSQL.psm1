#ps1_sysnative

# Copyright 2014 Cloudbase Solutions Srl
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

$ErrorActionPreference = 'Stop'

$modulePath = "heat-powershell-utils.psm1"
$currentLocation = Split-Path -Parent $MyInvocation.MyCommand.Path
$fullPath = Join-Path $currentLocation $modulePath
Import-Module -Name $fullPath -DisableNameChecking -Force

$heatTemplateName = "MSSQL"

function Log {
    param(
        $message
    )
    LogTo-File -LogMessage $message -Topic $heatTemplateName
    Log-HeatMessage $message
}

function Install-RequiredFeatures {
    param()

    $windowsFeatures = @('NET-Framework-Core')
    $installStatus = Install-WindowsFeatures $windowsFeatures
    if ($installStatus.Reboot -eq $true) {
        Log "System will reboot to finish install updates."
        ExitFrom-Script $rebootAndReexecuteCode
    }
}

function Add-MSSQLUser {
    param(
        $mssqlServiceUsername,
        $mssqlServicePassword
    )

    Log "Adding the MSSQL user."
    Add-WindowsUser $mssqlServiceUsername $mssqlServicePassword
}

function Copy-FilesLocal {
    param(
        $From
    )

    $copyLocal = ${ENV:Temp}
    $fileName = Split-Path -Path $From -Leaf
    $localPath = Join-Path -Path $copyLocal $fileName
    Copy-Item -Force -Recurse -Path $From -Destination $localPath
    Log ("Local iso path:" + $localPath)
    return $localPath
}

function Get-MSSQLParameters {
    param(
        $MssqlServiceUsername,
        $MssqlServicePassword,
        $MssqlSaPassword,
        $MssqlFeatures,
        $MssqlInstanceName
    )

    $parameters = "/ACTION=install "
    $parameters += "/Q "
    $parameters += "/IACCEPTSQLSERVERLICENSETERMS=1 "
    $parameters += "/INSTANCENAME=$MssqlInstanceName "
    $parameters += "/FEATURES=$MssqlFeatures "
    if (($MSSQLVersion -gt 12) -and($MssqlFeatures -split "," -contains "ADV_SSMS")) {
        Log "MSSQL 2016 is not compatible with ADV_SSMS feature"
    }
    $parameters += "/SQLSYSADMINACCOUNTS=Admin "
    if ($MSSQLVersion -gt 10) {
        $parameters += "/UpdateEnabled=1 "
    }
    $parameters += "/AGTSVCSTARTUPTYPE=Automatic "
    $parameters += "/BROWSERSVCSTARTUPTYPE=Automatic "
    $parameters += "/SECURITYMODE=SQL "
    $parameters += "/SAPWD=$MssqlSaPassword "
    $parameters += "/SQLSVCACCOUNT=.\$MssqlServiceUsername "
    $parameters += "/SQLSVCPASSWORD=$MssqlServicePassword "
    $parameters += "/SQLSVCSTARTUPTYPE=Automatic "
    $parameters += "/NPENABLED=1 "
    $parameters += "/TCPENABLED=1 /ERRORREPORTING=1"

    return $parameters
}

function Get-MSSQLError {
    param()

    $sqlErrorString = "Failed: see details below"
    $errorsCount = (Select-String $sqlErrorString -Path $sqlLogFile).Length
    if ($errorsCount -ne 0) {
        Log "MSSQL log file has an error."
        return $true
    }

    return $false
}

function Add-NetRules {
    param()
    Open-Port 80 "TCP" "HTTP"
    Open-Port 443 "TCP" "HTTPS"
    Open-Port 1434 "UDP" "SQL Browser"
    Open-Port 135 "TCP" "SQL Debugger/RPC"
    Open-Port 5355 "UDP" "Link Local Multicast Name Resolution"

    netsh.exe firewall set multicastbroadcastresponse ENABLE

    $sqlServerBinaryPath = Join-Path ${ENV:ProgramFiles} -ChildPath `
                             "Microsoft SQL Server\MSSQL11.MSSQL\MSSQL\Binn\sqlservr.exe"
    New-NetFirewallRule -DisplayName "Allow TCP Sql Server Ports" `
        -Direction Inbound -Action Allow -EdgeTraversalPolicy Allow `
        -Protocol UDP -LocalPort 100-65000 -Program $sqlServerBinaryPath
    New-NetFirewallRule -DisplayName "Allow TCP Sql Server Ports" `
        -Direction Inbound -Action Allow -EdgeTraversalPolicy Allow `
        -Protocol TCP -LocalPort 100-65000 -Program $sqlServerBinaryPath
}

function Load-XML {
    Param (
        [Parameter(Mandatory =$true)]
        [string]$XMLFile
        )
    $xml=New-Object System.Xml.XmlDataDocument
    $xml.Load($XMLFile)
    return $xml
}

function Get-MSSQlVersion {
    Param (
        [Parameter(Mandatory =$true)]
        [string]$MediaInfoXMLPath
        )
    if( -not (Test-Path $MediaInfoXMLPath)) {
        Log "MediaInfoXMLPath does not exist!"
    }
    $xml = Load-XML ($MediaInfoXMLPath)
    try {
        return $xml.MediaInfo.Properties.Property[1].Value.ToString().SubString(0,2)
    } catch {
        # Note: for MSSQL Server 2008, the value does not exist
        return 10
      }
}

function Get-MSSQLLogFile {
    Param (
        [Parameter(Mandatory =$true)]
        [string]$MSSQLVersion
        )
    $sqlLogFile = Join-Path ${ENV:ProgramFiles} -ChildPath `
                 ("\Microsoft SQL Server\{0}0\Setup Bootstrap\Log\Summary.txt" -f $MSSQLVersion)
    return $sqlLogFile
}

function Install-MSSQLInternal {
    param(
        $MssqlServiceUsername,
        $MssqlServicePassword,
        $MssqlSaPassword,
        $MssqlFeatures,
        $MssqlInstanceName,
        $MssqlIsoUNCPath,
        $MssqlWaitConditionEndpoint,
        $MssqlWaitConditionToken
    )

    Log "Started MSSQL instalation."

    Install-RequiredFeatures

    Add-MSSQLUser $MssqlServiceUsername $MssqlServicePassword

    $localIsoPath = Copy-FilesLocal $MssqlIsoUNCPath
    Log "MSSQL ISO Mount."
    $iso = Mount-DiskImage -PassThru $localIsoPath
    Get-PSDrive | Out-Null
    $driveLetter = (Get-Volume -DiskImage $iso).DriveLetter
    $MediaInfoXMLPath = $driveLetter + ":\MediaInfo.xml"
    $MSSQLVersion = Get-MSSQLVersion $MediaInfoXMLPath
    $isoSetupPath = $driveLetter + ":\setup.exe"
    $sqlLogFile= Get-MSSQLLogFile $MSSQLVersion

    if (Test-Path $sqlLogFile) {
        Remove-Item $sqlLogFile -Force
    }
    $parameters = Get-MSSQLParameters `
                      -MssqlServiceUsername $mssqlServiceUsername `
                      -MssqlServicePassword $mssqlServicePassword `
                      -MssqlSaPassword $mssqlSaPassword `
                      -MssqlFeatures $mssqlFeatures `
                      -MssqlInstanceName $mssqlInstanceName
    ExecuteWith-Retry -Command {
            param($isoSetupPath, $parameters)
            Start-Process -Wait -FilePath $isoSetupPath `
                -ArgumentList $parameters
        } -Arguments @($isoSetupPath, $parameters)

    Dismount-DiskImage -ImagePath $iso.ImagePath
    Remove-Item $localIsoPath

    if ((Get-MSSQLError) -eq $true) {
        throw "Failed to install MSSQL Server."
    }
    Add-NetRules

    $successMessage = "Finished MSSQL instalation."
    Log $successMessage
    Send-HeatWaitSignal -Endpoint $MssqlWaitConditionEndpoint `
        -Message $successMessage -Success $true `
        -Token $MssqlWaitConditionToken
}

function Install-MSSQL {
    param(
        $MssqlServiceUsername,
        $MssqlServicePassword,
        $MssqlSaPassword,
        $MssqlFeatures,
        $MssqlInstanceName,
        $MssqlIsoUNCPath,
        $MssqlWaitConditionEndpoint,
        $MssqlWaitConditionToken
    )

    try {
        Install-MSSQLInternal -MssqlServiceUsername $mssqlServiceUsername `
            -MssqlServicePassword $mssqlServicePassword `
            -MssqlSaPassword $mssqlSaPassword `
            -MssqlFeatures $mssqlFeatures `
            -MssqlInstanceName $mssqlInstanceName `
            -MssqlIsoUNCPath $mssqlIsoUNCPath `
            -MssqlWaitConditionEndpoint $mssqlWaitConditionEndpoint `
            -MssqlWaitConditionToken $MssqlWaitConditionToken
    } catch {
        Log "Failed to install template."
        Send-HeatWaitSignal -Endpoint $MssqlWaitConditionEndpoint `
            -Message $_.Exception.Message -Success $false `
            -Token $MssqlWaitConditionToken
    }
}

Export-ModuleMember -Function * -ErrorAction SilentlyContinue
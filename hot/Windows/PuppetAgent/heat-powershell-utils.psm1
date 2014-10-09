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

$rebotCode = 1001
$reexecuteCode = 1002
$rebootAndReexecuteCode = 1003

# UNTESTABLE METHODS

function ExitFrom-Script {
    param(
        [int]$ExitCode
    )

    exit $ExitCode
}

function Get-LastExitCode () {
    return $LASTEXITCODE
}

function Get-PSMajorVersion () {
    return $PSVersionTable.PSVersion.Major
}

function Open-FileForRead ($FilePath) {
    return [System.IO.File]::OpenRead($FilePath)
}

function Write-PrivateProfileString ($Section, $Key, $Value, $Path) {
    return [PSCloudbase.Win32IniApi]::WritePrivateProfileString(
                                            $Section, $Key, $Value, $Path)
}

function Get-LastError () {
    return [PSCloudbase.Win32IniApi]::GetLastError()
}

function Create-WebRequest ($Uri) {
    return [System.Net.WebRequest]::Create($Uri)
}

function Get-Encoding ($CodePage) {
    return [System.Text.Encoding]::GetEncoding($CodePage)
}

function Execute-Process ($DestinationFile, $Arguments) {
    if (($Arguments.Count -eq 0) -or ($Arguments -eq $null)) {
        $p = Start-Process -FilePath $DestinationFile `
                           -PassThru `
                           -Wait
    } else {
        $p = Start-Process -FilePath $DestinationFile `
                           -ArgumentList $Arguments `
                           -PassThru `
                           -Wait
    }

    return $p
}

# TESTABLE METHODS

function Log-HeatMessage {
    param(
        [string]$Message
    )

    Write-Host $Message
}

function ExecuteWith-Retry {
    param(
        [ScriptBlock]$Command,
        [int]$MaxRetryCount=10,
        [int]$RetryInterval=3,
        [array]$Arguments=@()
    )

    $currentErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    $retryCount = 0
    while ($true) {
        try {
            $res = Invoke-Command -ScriptBlock $Command `
                     -ArgumentList $Arguments
            $ErrorActionPreference = $currentErrorActionPreference
            return $res
        } catch [System.Exception] {
            $retryCount++
            if ($retryCount -gt $MaxRetryCount) {
                $ErrorActionPreference = $currentErrorActionPreference
                throw $_.Exception
            } else {
                Write-Error $_.Exception
                Start-Sleep $RetryInterval
            }
        }
    }
}

function Execute-ExternalCommand {
    param(
        [ScriptBlock]$Command,
        [array]$Arguments=@(),
        [string]$ErrorMessage
    )

    $res = Invoke-Command -ScriptBlock $Command -ArgumentList $Arguments
    if ((Get-LastExitCode) -ne 0) {
        throw $ErrorMessage
    }
    return $res
}

function Is-WindowsServer2008R2 () {
    $winVer = (Get-WmiObject -Class Win32_OperatingSystem).Version.Split('.')
    return (($winVer[0] -eq 6) -and ($winVer[1] -eq 1))
}

function Install-WindowsFeatures {
     param(
        [Parameter(Mandatory=$true)]
        [array]$Features,
        [int]$RebootCode=$rebootAndReexecuteCode
    )

    if ((Is-WindowsServer2008R2) -eq $true) {
        Import-Module -Name ServerManager
    }

    $rebootNeeded = $false
    foreach ($feature in $Features) {
        if ((Is-WindowsServer2008R2) -eq $true) {
            $state = ExecuteWith-Retry -Command {
                Add-WindowsFeature -Name $feature -ErrorAction Stop
            } -MaxRetryCount 13 -RetryInterval 2
        } else {
            $state = ExecuteWith-Retry -Command {
                Install-WindowsFeature -Name $feature -ErrorAction Stop
            } -MaxRetryCount 13 -RetryInterval 2
        }
        if ($state.Success -eq $true) {
            if ($state.RestartNeeded -eq 'Yes') {
                $rebootNeeded = $true
            }
        } else {
            throw "Install failed for feature $feature"
        }
    }

    if ($rebootNeeded -eq $true) {
        ExitFrom-Script -ExitCode $RebootCode
    }
}

function Copy-FileToLocal {
    param(
        $UNCPath
    )

    $tempLocation = ${ENV:Temp}
    $fileName = Split-Path -Path $UNCPath -Leaf
    $localPath = Join-Path -Path $tempLocation -ChildPath $fileName
    Copy-Item -Path $UNCPath -Destination $localPath -Recurse -Force

    Log-HeatMessage ("Local file path: " + $localPath)

    return $localPath
}

function Unzip-File {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ZipFile,
        [Parameter(Mandatory=$true)]
        [string]$Destination
    )

    $shellApp = New-Object -ComObject Shell.Application
    $zipFileNs = $shellApp.NameSpace($ZipFile)
    $destinationNS = $shellApp.NameSpace($Destination)
    $destinationNS.CopyHere($zipFileNs.Items(), 0x4)
}

function Download-File {
    param(
        [Parameter(Mandatory=$true)]
        [string]$DownloadLink,
        [Parameter(Mandatory=$true)]
        [string]$DestinationFile
    )

    $webclient = New-Object System.Net.WebClient
    ExecuteWith-Retry -Command {
        $webclient.DownloadFile($DownloadLink, $DestinationFile)
    } -MaxRetryCount 13 -RetryInterval 2
}

# Get-FileHash for Powershell versions less than 4.0 (SHA1 algorithm only)
function Get-FileSHA1Hash {
    [CmdletBinding()]
    param(
        [parameter(Mandatory=$true)]
        [string]$Path,
        [string]$Algorithm = "SHA1"
    )

    process
    {
        if ($Algorithm -ne "SHA1") {
            throw "Unsupported algorithm: $Algorithm"
        }
        $fullPath = Resolve-Path $Path
        $f = Open-FileForRead $fullPath
        $sham = $null
        try {
            $sham = New-Object System.Security.Cryptography.SHA1Managed
            $hash = $sham.ComputeHash($f)
            $hashSB = New-Object System.Text.StringBuilder `
                                -ArgumentList ($hash.Length * 2)
            foreach ($b in $hash) {
                $sb = $hashSB.AppendFormat("{0:x2}", $b)
            }
            return [PSCustomObject]@{ Algorithm = "SHA1";
                                      Hash = $hashSB.ToString().ToUpper();
                                      Path = $fullPath }
        }
        finally {
            $f.Close()
            if($sham) {
                $sham.Clear()
            }
        }
    }
}

function Check-FileIntegrityWithSHA1 {
    param(
        [Parameter(Mandatory=$true)]
        [string]$File,
        [Parameter(Mandatory=$true)]
        [string]$ExpectedSHA1Hash
    )

    if ((Get-PSMajorVersion) -lt 4) {
        $hash = (Get-FileSHA1Hash -Path $File).Hash
    } else {
        $hash = (Get-FileHash -Path $File -Algorithm "SHA1").Hash
    }
    if ($hash -ne $ExpectedSHA1Hash) {
        $errMsg = "SHA1 hash not valid for file: $filename. " +
                  "Expected: $ExpectedSHA1Hash Current: $hash"
        throw $errMsg
    }
}

function Install-Program {
    param(
        [Parameter(Mandatory=$true)]
        [string]$DownloadLink,
        [Parameter(Mandatory=$true)]
        [string]$DestinationFile,
        [Parameter(Mandatory=$true)]
        [string]$ExpectedSHA1Hash,
        [array]$Arguments,
        [Parameter(Mandatory=$true)]
        [string]$ErrorMessage
    )

    Download-File $DownloadLink $DestinationFile
    Check-FileIntegrityWithSHA1 $DestinationFile $ExpectedSHA1Hash
    $p = Execute-Process $DestinationFile $Arguments

    if ($p.ExitCode -ne 0) {
        throw $ErrorMessage
    }

    Remove-Item $DestinationFile
}

function Set-IniFileValue {
    [CmdletBinding()]
    param(
        [parameter(Mandatory=$true, ValueFromPipeline=$true)]
        [string]$Key,
        [parameter()]
        [string]$Section = "DEFAULT",
        [parameter(Mandatory=$true)]
        [string]$Value,
        [parameter(Mandatory=$true)]
        [string]$Path
    )

    process
    {
        $Source = @"
        using System;
        using System.Text;
        using System.Runtime.InteropServices;

        namespace PSCloudbase
        {
            public sealed class Win32IniApi
            {
                [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
                public static extern uint GetPrivateProfileString(
                   string lpAppName,
                   string lpKeyName,
                   string lpDefault,
                   StringBuilder lpReturnedString,
                   uint nSize,
                   string lpFileName);

                [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
                [return: MarshalAs(UnmanagedType.Bool)]
                public static extern bool WritePrivateProfileString(
                   string lpAppName,
                   string lpKeyName,
                   StringBuilder lpString, // Don't use string, as Powershell replaces $null with an empty string
                   string lpFileName);

                [DllImport("Kernel32.dll")]
                public static extern uint GetLastError();
            }
        }
"@
        Add-Type -TypeDefinition $Source -Language CSharp
        $retVal = Write-PrivateProfileString $Section $Key $Value $Path
        $lastError = Get-LastError
        if (!$retVal -and $lastError) {
            throw ("Cannot set value in ini file: " + $lastError)
        }
    }
}

function LogTo-File {
    param(
        $LogMessage,
        $LogFile = "C:\cfn\userdata.log",
        $Topic = "General"
    )

    $date = Get-Date
    $fullMessage = "$date | $Topic | $LogMessage"
    Add-Content -Path $LogFile -Value $fullMessage
}

function Open-Port($Port, $Protocol, $Name) {
    Execute-ExternalCommand -Command {
        netsh.exe advfirewall firewall add rule `
            name=$Name dir=in action=allow protocol=$Protocol localport=$Port
    } -ErrorMessage "Failed to add firewall rule"
}

function Add-WindowsUser {
    param(
        [parameter(Mandatory=$true)]
        [string]$Username,
        [parameter(Mandatory=$true)]
        [string]$Password
    )

    Execute-ExternalCommand -Command {
        NET.EXE USER $Username $Password '/ADD'
    } -ErrorMessage "Failed to create new user"
}

# Invoke-RestMethod for Powershell versions less than 4.0
function Invoke-RestMethodWrapper {
    param(
        [Uri]$Uri,
        [Object]$Body,
        [System.Collections.IDictionary]$Headers,
        [string]$Method
    )

    $request = Create-WebRequest $Uri
    $request.Method = $Method
    foreach ($key in $Headers.Keys) {
        try {
            $request.Headers.Add($key, $Headers[$key])
        } catch {
            $property = $key.Replace('-', '')
            $request.$property = $Headers[$key]
        }
    }

    if (($Body -ne $null) -and ($Method -eq "POST")) {
        $encoding = Get-Encoding "UTF-8"
        $bytes = $encoding.GetBytes($Body)
        $request.ContentLength = $bytes.Length
        $writeStream = $request.GetRequestStream()
        $writeStream.Write($bytes, 0, $bytes.Length)
    }

    $response = $request.GetResponse()
    $requestStream = $response.GetResponseStream()
    $readStream = New-Object System.IO.StreamReader $requestStream
    $data = $readStream.ReadToEnd()

    return $data
}

function Invoke-HeatRestMethod {
    param(
        $Endpoint,
        [System.String]$HeatMessageJSON,
        [System.Collections.IDictionary]$Headers
    )

    if ((Get-PSMajorVersion) -lt 4) {
        $result = Invoke-RestMethodWrapper -Method "POST" `
                                           -Uri $Endpoint `
                                           -Body $HeatMessageJSON `
                                           -Headers $Headers
    } else {
        $result = Invoke-RestMethod -Method "POST" `
                                    -Uri $Endpoint `
                                    -Body $HeatMessageJSON `
                                    -Headers $Headers
    }
}

function Send-HeatWaitSignal {
    param(
        [parameter(Mandatory=$true)]
        [string]$Endpoint,
        [parameter(Mandatory=$true)]
        [string]$Token,
        $Message,
        $Success=$true
    )

    $statusMap = @{
        $true="SUCCESS";
        $false="FAILURE"
    }

    $heatMessage = @{
        "status"=$statusMap[$Success];
        "reason"="Configuration script has been executed.";
        "data"=$Message;
    }
    $headers = @{
        "X-Auth-Token"=$Token;
        "Accept"="application/json";
        "Content-Type"= "application/json";
    }
    $heatMessageJSON = ConvertTo-JSON -InputObject $heatMessage

    Invoke-HeatRestMethod -Endpoint $Endpoint `
                          -HeatMessageJSON $heatMessageJSON `
                          -Headers $headers
}

Export-ModuleMember -Function *

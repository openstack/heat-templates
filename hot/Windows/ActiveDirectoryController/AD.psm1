#ps1_sysnative

# Copyright 2016 Cloudbase Solutions Srl
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
$rebootCode = 1003

function Install-ActiveDirectoryDomainController {

    param(
        $SafeModePwd,
        $DomainName,
        $DomainNetbiosName,
        $ADWaitConditionEndpoint,
        $ADWaitConditionToken
    )
    try {
        if (Is-DomainInstalled -fullDomainName $DomainName) {
            Send-HeatWaitSignal -Endpoint $ADWaitConditionEndpoint `
                -Message "Active Directory has been successfully installed" `
                -Success $true -Token $ADWaitConditionToken
        } else {
            Install-WindowsFeature -Name AD-Domain-Services -IncludeManagementTools
            $defaultLocalAdministrator = Get-DefaultLocalAdministrator
            $localAdministratorPath = "WinNT://./$defaultLocalAdministrator"
            $user = [ADSI]$localAdministratorPath
            $user.SetPassword($SafeModePwd)
            Import-Module ADDSDeployment
            $secureSafeModePwd = ConvertTo-SecureString $SafeModePwd -AsPlainText -Force
            Install-ADDSForest -DomainName $DomainName `
                -DomainNetbiosName $DomainNetbiosName `
                -SafeModeAdministratorPassword $secureSafeModePwd `
                -InstallDns -NoRebootOnCompletion -Force
            exit $rebootCode
        }
    } catch {
        Write-Host $_
        Send-HeatWaitSignal -Endpoint $ADWaitConditionEndpoint `
            -Message "Active Directory could not be installed" -Success $false `
            -Token $ADWaitConditionToken
        exit 1
    }
}

function Execute-Retry {
    Param(
        [parameter(Mandatory=$true)]
        $command,
        [int]$maxRetryCount=4,
        [int]$retryInterval=4
    )

    $currErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    $retryCount = 0
    while ($true) {
        try {
            $res = Invoke-Command -ScriptBlock $command
            $ErrorActionPreference = $currErrorActionPreference
            return $res
        } catch [System.Exception] {
            $retryCount++
            if ($retryCount -ge $maxRetryCount) {
                $ErrorActionPreference = $currErrorActionPreference
                throw
            } else {
                if($_) {
                    Write-Warning $_
                }
                Start-Sleep $retryInterval
            }
        }
    }
}

function Is-DomainInstalled {
    param(
        [string]$fullDomainName
        )
    $isForestInstalled = $true
    try {
        $isForestInstalled = Execute-Retry {
            if (!(Get-Command Get-ADForest -ErrorAction SilentlyContinue)) {
                return $false }
            $forestName = (Get-ADForest).Name
            if ($forestName -ne $fullDomainName) {
                return $false
            } else {
                return $true
            }
        } -retryInterval 10
    } catch {
        $isForestInstalled = $false
        Write-Host $_
    }
    return $isForestInstalled
}

function Get-DefaultLocalAdministrator {
    $administratorsGroupSID = "S-1-5-32-544"
    $group = Get-CimInstance -ClassName Win32_Group  `
                -Filter "SID = '$administratorsGroupSID'"
    $localAdministrator = Get-CimAssociatedInstance -InputObject $group `
        -ResultClassName Win32_UserAccount | Where-Object `
        { $_.SID.StartsWith("S-1-5-21") -and $_.SID.EndsWith("-500") }
    if ($localAdministrator) {
        return $localAdministrator.Name
    } else {
        throw "Failed to get default local administrator"
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
    $heatMessageJSON = $heatMessage | ConvertTo-JSON
    $result = Invoke-RestMethod -Method POST -Uri $Endpoint `
                -Body $heatMessageJSON -Headers $headers
}

Export-ModuleMember -Function *


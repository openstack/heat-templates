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

$heatTemplateName = "PuppetAgent"
$puppetAgentMsiUrl = "https://downloads.puppetlabs.com/windows/" + `
                          "puppet-latest.msi"
$puppetAgentMsiPath = Join-Path $ENV:TEMP "puppet_agent.msi"
$puppetAgentInstallLogFile = Join-Path $ENV:TEMP "puppet_agent_msi_log.txt"
$hostsFile = "$ENV:SystemRoot\System32\Drivers\etc\hosts"

function Log {
    param(
        $message
    )
    LogTo-File -LogMessage $message -Topic $heatTemplateName
    Log-HeatMessage $message
}

function Install-PuppetAgentInternal {
    param(
        $PuppetMasterServerName,
        $PuppetMasterServerIp
    )

    if ($PuppetMasterServerIp) {
        $ip = [System.Net.IPAddress]::Parse($PuppetMasterServerIp)
        Add-Content -Path $hostsFile `
            -Value "$PuppetMasterServerIp $PuppetMasterServerName"
    }

    Download-File $puppetAgentMsiUrl $puppetAgentMsiPath
    Execute-ExternalCommand {
        param($PuppetMasterServerName,
              $PuppetAgentInstallLogFile)
        cmd /c start /wait msiexec /qn /i $puppetAgentMsiPath `
            /l*v $PuppetAgentInstallLogFile `
            PUPPET_MASTER_SERVER=$PuppetMasterServerName
     } -Arguments @($PuppetMasterServerName, $puppetAgentInstallLogFile) `
       -ErrorMessage "Puppet Agent install failed."
}

function Install-PuppetAgent {
    param(
        $PuppetMasterServerName,
        $PuppetMasterServerIp,
        $PuppetAgent_WaitConditionEndpoint,
        $PuppetAgent_WaitConditionToken
    )

    try {
        Log "Puppet agent installation started"
        Install-PuppetAgentInternal `
            -PuppetMasterServerName $puppetMasterServerName `
            -PuppetMasterServerIp $puppetMasterServerIp

        $successMessage = "Finished Puppet Agent installation"
        Log $successMessage
        Send-HeatWaitSignal -Endpoint $PuppetAgent_WaitConditionEndpoint `
                            -Message $successMessage `
                            -Success $true `
                            -Token $PuppetAgent_WaitConditionToken

    } catch {
        $failMessage = "Installation encountered an error"
        Log $failMessage
        Log "Exception details: $_.Exception.Message"
        Send-HeatWaitSignal -Endpoint $PuppetAgent_WaitConditionEndpoint `
                            -Message $_.Exception.Message `
                            -Success $false `
                            -Token $PuppetAgent_WaitConditionToken
    }
}

Export-ModuleMember -Function Install-PuppetAgent -ErrorAction SilentlyContinue


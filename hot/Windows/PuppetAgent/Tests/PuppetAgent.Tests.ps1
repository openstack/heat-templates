#ps1_sysnative

<#
Copyright 2014 Cloudbase Solutions Srl

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
#>

$utilsPath = (Resolve-Path '..\heat-powershell-utils.psm1').Path
$modulePath = (Resolve-Path '..\PuppetAgent.psm1').Path

Remove-Module PuppetAgent -ErrorAction SilentlyContinue
Remove-Module heat-powershell-utils -ErrorAction SilentlyContinue
Import-Module -Name $modulePath -DisableNameChecking
Import-Module -Name $utilsPath -DisableNameChecking

InModuleScope PuppetAgent {
    Describe "Install-PuppetAgent" {
        Context "Puppet Agent installed" {
            $puppetMasterServerName = "puppet_master_server_hostname"
            $puppetMasterServerIp = "puppet_master_server_ip_address"
            $puppetAgent_WaitConditionEndpoint = `
                "puppet_agent_wait_condition_endpoint"
            $puppetAgent_WaitConditionToken = `
                "puppet_agent_wait_condition_token"

            Mock Log { return 0 } -Verifiable
            Mock Send-HeatWaitSignal { return 0 } -Verifiable
            Mock Install-PuppetAgentInternal { return 0 } -Verifiable

            Install-PuppetAgent `
            -PuppetMasterServerName $puppetMasterServerName `
            -PuppetMasterServerIp $puppetMasterServerIp `
            -PuppetAgent_WaitConditionEndpoint `
                $puppetAgent_WaitConditionEndpoint `
            -PuppetAgent_WaitConditionToken $puppetAgent_WaitConditionToken

            It "should verify mocks called" {
                Assert-VerifiableMocks
            }

        }
    }
}

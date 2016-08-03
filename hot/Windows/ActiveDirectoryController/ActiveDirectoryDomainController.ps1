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

$moduleName = "AD.psm1"
$cfnFolder = "C:\cfn"
$modulePath = Join-Path $cfnFolder $moduleName
Import-Module -Name $modulePath -DisableNameChecking -Force


$safeModePwd = "safe_mode_administrator_password"
$DomainName = "domain_name"
$DomainNetbiosName = "domain_netbios_name"
$ADWaitConditionEndpoint = "ad_wait_condition_endpoint"
$ADWaitConditionToken = "ad_wait_condition_token"

Install-ActiveDirectoryDomainController -SafeModePwd $safeModePwd `
    -DomainName $DomainName `
    -DomainNetbiosName $DomainNetbiosName `
    -ADWaitConditionEndpoint $ADWaitConditionEndpoint `
    -ADWaitConditionToken $ADWaitConditionToken


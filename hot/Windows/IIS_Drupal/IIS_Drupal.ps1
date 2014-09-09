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

$ErrorActionPreference = 'Stop'

$cfnFolder = Join-Path $env:SystemDrive "cfn"
$moduleName = "IIS_Drupal.psm1"
$modulePath = Join-Path $cfnFolder $moduleName
Import-Module -Name $modulePath -DisableNameChecking

$parameters = @{
    'ENDPOINT'    = 'wait_handle_endpoint';
    'TOKEN'       = 'wait_handle_token';
    'SA_PASS'     = 'sa_password';
    'ADMIN_USER'  = 'admin_username';
    'ADMIN_PASS'  = 'admin_password';
    'ADMIN_EMAIL' = 'admin_email';
    'SITE_NAME'   = 'website_name'
}

Initialize-Server $parameters

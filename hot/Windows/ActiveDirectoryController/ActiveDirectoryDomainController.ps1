#ps1_sysnative
$ErrorActionPreference = 'Stop'
$rebootCode = 1001
Install-WindowsFeature -Name AD-Domain-Services -IncludeManagementTools

$user = [ADSI]'WinNT://./Administrator'
$user.SetPassword('safe_mode_administrator_password')

Import-Module ADDSDeployment
$safeModePwd = (ConvertTo-SecureString 'safe_mode_administrator_password' -AsPlainText -Force)
Install-ADDSForest -DomainName 'domain_name' -DomainNetbiosName 'domain_netbios_name' -SafeModeAdministratorPassword $safeModePwd -InstallDns -NoRebootOnCompletion -Force

exit $rebootCode

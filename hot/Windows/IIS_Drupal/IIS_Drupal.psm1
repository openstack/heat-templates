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

$cfnFolder = Join-Path $env:SystemDrive "cfn"
$moduleName = "heat-powershell-utils.psm1"
$modulePath = Join-Path $cfnFolder $moduleName
Import-Module -Name $modulePath `
              -DisableNameChecking `
              -ErrorAction SilentlyContinue

# In case download links change or become unavailable,
# they must be updated and new expected SHA1 hashes must be computed.
$downloadLinks = @{
    'SQLEXPRESS08'  = 'http://download.microsoft.com/download/0/4/B/04BE03CD-EAF3-4797-9D8D-2E08E316C998/SQLEXPR_x64_ENU.exe';
    'SQLDRIVERS'    = 'http://download.microsoft.com/download/C/D/B/CDB0A3BB-600E-42ED-8D5E-E4630C905371/SQLSRV30.EXE';
    'PHP54'         = 'http://windows.php.net/downloads/releases/archives/php-5.4.33-nts-Win32-VC9-x86.zip';
    'VC2008SP1'     = 'http://download.microsoft.com/download/d/d/9/dd9a82d0-52ef-40db-8dab-795376989c03/vcredist_x86.exe';
    'UR20'          = 'http://download.microsoft.com/download/6/7/D/67D80164-7DD0-48AF-86E3-DE7A182D6815/rewrite_2.0_rtw_x64.msi';
    'DRUSH'         = 'https://github.com/drush-ops/drush/releases/download/6.0.0/Drush-6.0-2013-08-28-Installer-v1.0.21.msi';
    'DRUPALDRIVERS' = 'http://ftp.drupal.org/files/projects/sqlsrv-7.x-1.x-dev.zip';
    'DRUPAL'        = 'https://ftp.drupal.org/files/projects/drupal-7.50.zip';
    'SQLNCLI12'     = 'http://download.microsoft.com/download/4/B/1/4B1E9B0E-A4F3-4715-B417-31C82302A70A/ENU/x64/sqlncli.msi';
    '7Z'            = 'http://kent.dl.sourceforge.net/project/sevenzip/7-Zip/9.20/7z920.msi'
}

$sha1Hashes = @{
    'SQLEXPRESS08'  = 'E768A3B70E3F3B596EFFA9F57D812F95C0A0506B';
    'SQLDRIVERS'    = '1457A9F9B87119265966EEE6C9A648249A7A83E0';
    'PHP54'         = 'F414F9CC3585CBE511E6C183261F347BAE071784';
    'VC2008SP1'     = '6939100E397CEF26EC22E95E53FCD9FC979B7BC9';
    'UR20'          = '84BDEAEF26BCB2CB60BB8686EAF6194607F7F003';
    'DRUSH'         = 'CA71B7AFAAF18904B23DDB9224E030C97978AC89';
    'DRUPALDRIVERS' = '8DAD020F8F4C1F1BEEE081AC21C660F5E5063796';
    'DRUPAL'        = 'BC6D1B3B2A43FD81E1DA7CF69028C8DCFB45D594';
    'SQLNCLI12'     = '789CD5F898F80A799F0288F140F3FBCDF0473DE8';
    '7Z'            = 'C67D3F611EA3EB3336CF92F6FFCAFDB14F8B12AF'
}

function Install-IIS () {
    LogTo-File "Install IIS windows features"

    Install-WindowsFeatures `
        -Features @("Web-Server",
                    "Web-Http-Redirect",
                    "Web-DAV-Publishing",
                    "Web-Custom-Logging",
                    "Web-Log-Libraries",
                    "Web-ODBC-Logging",
                    "Web-Request-Monitor",
                    "Web-Http-Tracing",
                    "Web-Mgmt-Console",
                    "Web-Scripting-Tools",
                    "Web-Mgmt-Service",
                    "Web-CGI",
                    "NET-Framework-Core")
}

function Install-SQLServerExpress2008R2SP2 ($SAPassword) {
    LogTo-File "Install SQL Server Express 2008 R2 SP2"

    $file = Join-Path $env:TEMP $downloadLinks['SQLEXPRESS08'].Split('/')[-1]
    Install-Program `
        -DownloadLink $downloadLinks['SQLEXPRESS08'] `
        -DestinationFile $file `
        -ExpectedSHA1Hash $sha1Hashes['SQLEXPRESS08'] `
        -Arguments @('/ACTION=Install',
                     '/Q',
                     '/IACCEPTSQLSERVERLICENSETERMS',
                     '/INSTANCENAME=SQLEXPRESS',
                     '/SECURITYMODE=SQL',
                     "/SAPWD=$SAPassword",
                     '/SQLSYSADMINACCOUNTS="BUILTIN\Administrators"') `
        -ErrorMessage "Failed to install SQL Server 2008 R2 SP2 Express"

    $sqlEnvPath =
        ";${env:ProgramFiles(x86)}\Microsoft SQL Server\100\Tools\Binn\" +
        ";$env:ProgramFiles\Microsoft SQL Server\100\Tools\Binn\" +
        ";$env:ProgramFiles\Microsoft SQL Server\100\DTS\Binn\"
    $env:Path += $sqlEnvPath
}

function Install-SevenZip () {
    LogTo-File "Install 7-Zip"

    $file = Join-Path $env:TEMP $downloadLinks['7Z'].Split('/')[-1]
    Install-Program `
        -DownloadLink $downloadLinks['7Z'] `
        -DestinationFile $file `
        -ExpectedSHA1Hash $sha1Hashes['7Z'] `
        -Arguments @("/Q") `
        -ErrorMessage "Failed to install 7-Zip 9.20"
}

function Install-SQLServerDriversForPHP ($ExtLocation) {
    LogTo-File "Install SQL Server drivers for PHP"

    $SQLDriversPath = Join-Path $env:TEMP "SQLDrivers"
    $file = Join-Path $env:TEMP $downloadLinks['SQLDRIVERS'].Split('/')[-1]
    Install-Program `
        -DownloadLink $downloadLinks['SQLDRIVERS'] `
        -DestinationFile $file `
        -ExpectedSHA1Hash $sha1Hashes['SQLDRIVERS'] `
        -Arguments @("/Q",
                     "/T:$SQLDriversPath",
                     "/C") `
        -ErrorMessage "Failed to extract drivers into the specified path"

    $sqlsrv = Join-Path $SQLDriversPath "php_sqlsrv_54_nts.dll"
    $sqlsrvPDO = Join-Path $SQLDriversPath "php_pdo_sqlsrv_54_nts.dll"
    Copy-Item $sqlsrv $ExtLocation
    Copy-Item $sqlsrvPDO $ExtLocation
    Remove-Item $SQLDriversPath -Recurse
}

function Add-PHPSettings ($Settings, $SectionName="DEFAULT", $IniPath) {
    foreach ($key in $Settings.Keys) {
        Set-IniFileValue -Path $IniPath `
                         -Section $SectionName `
                         -Key $key `
                         -Value $Settings[$key]
    }
}

function Enable-PHPExtensions ($Extensions, $IniPath) {
    foreach ($key in $Extensions.Keys) {
        Set-IniFileValue -Path $IniPath `
                         -Section $key `
                         -Key "extension" `
                         -Value $Extensions[$key]
    }
}

function Configure-PHP54 ($PHPLocation, $ExtLocation) {
    LogTo-File "Configure PHP for IIS"

    $PHPIni = Join-Path $PHPLocation "php.ini"
    $oldPHPIni = Join-Path $PHPLocation "php.ini-production"
    Copy-Item $oldPhpIni $PHPIni

    Set-IniFileValue -Path $PHPIni `
                     -Section "PHP" `
                     -Key "memory_limit" `
                     -Value "128M"

    $settings = @{
        "error_log" = "$env:SystemRoot\temp\PHP_errors.log";
        "upload_tmp_dir" = "$env:SystemRoot\temp";
        "session.save_path" = "$env:SystemRoot\temp";
        "cgi.force_redirect" = 0;
        "cgi.fix_pathinfo" = 1;
        "fastcgi.impersonate" = 1;
        "fastcgi.logging" = 0;
        "max_execution_time" = 300;
        "extension_dir" = $ExtLocation }
    Add-PHPSettings -Settings $settings `
                    -IniPath $PHPIni

    $extensions = @{
        'MYSQL' = 'php_mysql.dll';
        'MYSQLI' = 'php_mysqli.dll';
        'SQLSRV_54_NTS' = 'php_sqlsrv_54_nts.dll';
        'MBSTRING' = 'php_mbstring.dll';
        'GD2' = 'php_gd2.dll';
        'GETTEXT' = 'php_gettext.dll';
        'CURL' = 'php_curl.dll';
        'EXIF' = 'php_exif.dll';
        'XMLRPC' = 'php_xmlrpc.dll';
        'OPENSSL' = 'php_openssl.dll';
        'SOAP' = 'php_soap.dll';
        'PDO_MYSQL' = 'php_pdo_mysql.dll';
        'PDO_SQLITE' = 'php_pdo_sqlite.dll';
        'PDO_SQLSRV_54_NTS' = 'php_pdo_sqlsrv_54_nts.dll';
        'IMAP' = 'php_imap.dll';
        'TIDY' = 'php_tidy.dll'}
    Enable-PHPExtensions -Extensions $extensions `
                         -IniPath $PHPIni

    $appcmd = Join-Path $env:SystemRoot "system32\inetsrv\appcmd.exe"
    Execute-Command -Command {
        & $appcmd set config /section:system.webServer/fastCGI `
            /+"[fullPath='$PHPLocation\php-cgi.exe']"
    } -ErrorMessage "Error occurred while creating FastCGI IIS process pool"

    Execute-Command -Command {
        & $appcmd set config /section:system.webServer/handlers `
        /+"[name='PHP_via_FastCGI', `
            path='*.php', `
            verb='*', `
            modules='FastCgiModule', `
            scriptProcessor='$PHPLocation\php-cgi.exe', `
            resourceType='Either']"
    } -ErrorMessage "Failed to create IIS handler mapping for PHP requests"

    Execute-Command -Command {
        & $appcmd set config -section:system.webServer/fastCgi `
            "/[fullPath='$PHPLocation\php-cgi.exe'].instanceMaxRequests:10000"
    } -ErrorMessage "Failed to set php-cgi InstanceMaxRequests"

    Execute-Command -Command {
        $cmd = "[fullPath='$PHPLocation\php-cgi.exe'].environmentVariables." +
               "[name='PHP_FCGI_MAX_REQUESTS',value='10000']"
        & $appcmd set config -section:system.webServer/fastCgi /+$cmd
    } -ErrorMessage "Failed to set PHP_FCGI_MAX_REQUESTS environment variable"
}

function Install-PHP54 ($PHPLocation) {
    LogTo-File "Install PHP 5.4"

    New-Item -ItemType Directory -Path $PHPLocation

    $phpZip = Join-Path $env:TEMP $downloadLinks['PHP54'].Split('/')[-1]
    Download-File $downloadLinks['PHP54'] $phpZip
    Check-FileIntegrityWithSHA1 $phpZip $sha1Hashes['PHP54']
    Unzip-File $phpZip $PHPLocation
    Remove-Item -Path $phpZip

    $extLocation = Join-Path $PHPLocation "ext"
    Install-SQLServerDriversForPHP -ExtLocation $extLocation
    Configure-PHP54 -PHPLocation $PHPLocation `
                    -ExtLocation $extLocation
}

function Install-Drupal7 {
    param(
        [string]$SAPassword,
        [string]$AdminUsername,
        [string]$AdminPassword,
        [string]$AdminEmail,
        [string]$WebsiteName
    )

    LogTo-File "Install Drupal 7"

    $file = Join-Path $env:TEMP $downloadLinks['VC2008SP1'].Split('/')[-1]
    Install-Program `
        -DownloadLink $downloadLinks['VC2008SP1'] `
        -DestinationFile $file `
        -ExpectedSHA1Hash $sha1Hashes['VC2008SP1'] `
        -Arguments "/q" `
        -ErrorMessage "Microsoft Visual C++ 2008 SP1 failed to install"

    $file = Join-Path $env:TEMP $downloadLinks['UR20'].Split('/')[-1]
    Install-Program `
        -DownloadLink $downloadLinks['UR20'] `
        -DestinationFile $file `
        -ExpectedSHA1Hash $sha1Hashes['UR20'] `
        -Arguments "/q" `
        -ErrorMessage "URL Rewrite 2.0 failed to install"

    $file = Join-Path $env:TEMP $downloadLinks['SQLNCLI12'].Split('/')[-1]
    Install-Program `
        -DownloadLink $downloadLinks['SQLNCLI12'] `
        -DestinationFile $file `
        -ExpectedSHA1Hash $sha1Hashes['SQLNCLI12'] `
        -Arguments @("/q",
                     "ADDLOCAL=ALL",
                     "IACCEPTSQLNCLILICENSETERMS=YES") `
        -ErrorMessage "SQL Server 2012 Native Client failed to install"

    $drupalVer = $downloadLinks['DRUPAL'].Split('/')[-1].Trim('.zip')
    $drupalZip = Join-Path $env:TEMP ($drupalVer + ".zip")
    Download-File $downloadLinks['DRUPAL'] $drupalZip
    Check-FileIntegrityWithSHA1 $drupalZip $sha1Hashes['DRUPAL']
    Unzip-File $drupalZip $env:TEMP

    $drupal7 = Join-Path $env:SystemDrive "inetpub\wwwroot\drupal7"
    New-Item -ItemType Directory -Path $drupal7
    $drupalTemp = Join-Path $env:TEMP $drupalVer
    Copy-Item "$drupalTemp\*" $drupal7 -Recurse
    Remove-Item $drupalTemp -Recurse
    Remove-Item $drupalZip

    $defaultPath = Join-Path $drupal7 "sites\default"
    $oldSettings = Join-Path $defaultPath "default.settings.php"
    $settings = Join-Path $defaultPath "settings.php"
    Copy-Item $oldSettings $settings

    $sqlDriversZip = Join-Path $env:TEMP `
                               $downloadLinks['DRUPALDRIVERS'].Split('/')[-1]
    Download-File $downloadLinks['DRUPALDRIVERS'] $sqlDriversZip
    Check-FileIntegrityWithSHA1 $sqlDriversZip $sha1Hashes['DRUPALDRIVERS']
    Unzip-File $sqlDriversZip "$drupal7\sites\all\modules"
    Copy-Item "$drupal7\sites\all\modules\sqlsrv\sqlsrv" `
              "$drupal7\includes\database" -Recurse
    Remove-Item $sqlDriversZip

    $appcmd = Join-Path $env:SystemRoot "system32\inetsrv\appcmd.exe"
    Execute-Command -Command {
        & $appCmd delete site 'Default Web Site'
    } -ErrorMessage "Failed to delete default web site"

    Execute-Command -Command {
        & $appCmd add site /site.name:'Drupal7' `
             /+"bindings.[protocol='http', bindingInformation='*:80:']" `
             /physicalPath:"$drupal7"
    } -ErrorMessage "Failed to create Drupal web site"

    Execute-Command -Command {
        & $appcmd add apppool /name:'Drupal7' /managedRuntimeVersion:'' `
                              /managedPipelineMode:Integrated
    } -ErrorMessage "Failed to create Drupal application pool"

    Execute-Command -Command {
        & $appCmd set site /site.name:'Drupal7' `
                           /"[path='/']".applicationPool:'Drupal7'
    } -ErrorMessage "Failed to assign website to Drupal application pool"

    Execute-Command -Command {
        icacls.exe $defaultPath /grant "IUSR:(OI)(CI)(M)"
    } -ErrorMessage "Failed to set permissions"

    Execute-Command -Command {
        iisreset.exe /restart
    } -ErrorMessage "Failed to restart IIS server"

    LogTo-File "Create Drupal database"

    $query = "USE [master]
              GO
              CREATE DATABASE drupal
              GO"
    Execute-Command -Command {
        SQLCMD.EXE -S '.\SQLEXPRESS' -Q $query
    } -ErrorMessage "Failed to create Drupal database and user"

    $file = Join-Path $env:TEMP $downloadLinks['DRUSH'].Split('/')[-1]
    Install-Program `
        -DownloadLink $downloadLinks['DRUSH'] `
        -DestinationFile $file `
        -ExpectedSHA1Hash $sha1Hashes['DRUSH'] `
        -Arguments "/q" `
        -ErrorMessage "Drush failed to install"

    $drushEnvPath = ";$env:ProgramData\Drush\" +
                    ";${env:ProgramFiles(x86)}\Drush\GnuWin32\bin" +
                    ";$env:SystemDrive\PHP\PHP54"
    $env:Path += $drushEnvPath

    LogTo-File "Start configure Drupal website with Drush"

    Push-Location $drupal7
    $drush = Join-Path $env:ProgramData "Drush\drush.bat"
    $dbUrl = "sqlsrv://sa:$SAPassword@.\SQLEXPRESS/drupal"
    Execute-Command -Command {
        & $drush site-install standard `
          install_configure_form.update_status_module='array(FALSE,FALSE)' `
                              --db-url=$dbUrl `
                              --account-mail=$AdminEmail `
                              --account-name=$AdminUsername `
                              --account-pass=$AdminPassword `
                              --site-name="$WebsiteName" `
                              --site-mail=$AdminEmail `
                              --yes
    } -ErrorMessage "Failed to configure Drupal site with drush"


    $tempFolder = Join-Path $defaultPath "files\tmp"
    New-Item -ItemType Directory -Path $tempFolder
    Execute-Command -Command {
        & $drush vset file_temporary_path $tempFolder
    } -ErrorMessage "Failed to set Drupal temporary folder"

    Pop-Location
}

function Install-IISWithDrupal ($parameters) {
    $PHPLocation = Join-Path $env:SystemDrive "PHP\PHP54"

    Install-IIS
    Install-SQLServerExpress2008R2SP2 -SAPassword $parameters['SA_PASS']
    Install-SevenZip
    Install-PHP54 -PHPLocation $PHPLocation
    Install-Drupal7 -SAPassword $parameters['SA_PASS'] `
                    -AdminUsername $parameters['ADMIN_USER'] `
                    -AdminPassword $parameters['ADMIN_PASS'] `
                    -AdminEmail $parameters['ADMIN_EMAIL'] `
                    -WebsiteName $parameters['SITE_NAME']
}

function Initialize-Server ($parameters) {
    try {
        LogTo-File "IIS with Drupal installation started"

        Install-IISWithDrupal $parameters

        $successMessage = "Finished IIS with Drupal installation"
        LogTo-File $successMessage
        Send-HeatWaitSignal -Endpoint $parameters['ENDPOINT'] `
                            -Message $successMessage `
                            -Success $true `
                            -Token $parameters['TOKEN']
    } catch {
        $failMessage = "IIS with Drupal installation encountered an error"
        LogTo-File $failMessage
        LogTo-File "Exception details: $_.Exception.Message"

        Send-HeatWaitSignal -Endpoint $parameters['ENDPOINT'] `
                            -Message $_.Exception.Message `
                            -Success $false `
                            -Token $parameters['TOKEN']
    }
}

Export-ModuleMember -Function Initialize-Server

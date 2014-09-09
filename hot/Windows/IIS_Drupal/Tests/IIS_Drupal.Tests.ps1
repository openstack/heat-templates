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

$utilsPath = (Resolve-Path '..\Common\heat-powershell-utils.psm1').Path
$modulePath = (Resolve-Path '..\IIS_Drupal.psm1').Path

Remove-Module IIS_Drupal -ErrorAction SilentlyContinue
Remove-Module heat-powershell-utils -ErrorAction SilentlyContinue
Import-Module -Name $modulePath -DisableNameChecking
Import-Module -Name $utilsPath -DisableNameChecking

InModuleScope IIS_Drupal {
    Describe "Install-IIS" {
        Context "IIS is installed" {
            Mock LogTo-File { return 0 } -Verifiable
            Mock Install-WindowsFeatures { return 0 } -Verifiable

            $IISFeatures = @("Web-Server",
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
            Install-IIS

            It "should install all the features" {
                Assert-MockCalled Install-WindowsFeatures -Exactly 1 `
                    -ParameterFilter { (((Compare-Object `
                        $Features $IISFeatures).InputObject).Length -eq 0) }
            }

            It "should log to file" {
                Assert-MockCalled LogTo-File -Exactly 1
            }
        }
    }

    Describe "Install-SQLServerExpress2008R2SP2" {
        Context "SQLEXPRESS is installed" {
            Mock LogTo-File { return 0 } -Verifiable
            Mock Install-Program { return 0 } -Verifiable
            $fakeSAPassword = 'password'

            $link = 'http://download.microsoft.com/download/0/4/B/' +
                    '04BE03CD-EAF3-4797-9D8D-2E08E316C998/SQLEXPR_x64_ENU.exe'
            $hash = 'E768A3B70E3F3B596EFFA9F57D812F95C0A0506B'
            $file = Join-Path $env:TEMP $link.Split('/')[-1]
            $sqlArguments = @('/ACTION=Install',
                             '/Q',
                             '/IACCEPTSQLSERVERLICENSETERMS',
                             '/INSTANCENAME=SQLEXPRESS',
                             '/SECURITYMODE=SQL',
                             "/SAPWD=$fakeSAPassword",
                             '/SQLSYSADMINACCOUNTS="BUILTIN\Administrators"')
            $sqlError = "Failed to install SQL Server 2008 R2 SP2 Express"
            Install-SQLServerExpress2008R2SP2 $fakeSAPassword

            It "should successfully install the program" {
                Assert-MockCalled Install-Program -Exactly 1 -ParameterFilter `
                    { ($DownloadLink -eq $link) -and
                      ($ExpectedSHA1Hash -eq $hash) -and
                      ($DestinationFile -eq $file) -and
                      ($ErrorMessage -eq $sqlError) -and
                      (((Compare-Object `
                        $sqlArguments $Arguments).InputObject).Length -eq 0) }
            }

            It "should log to file" {
                Assert-MockCalled LogTo-File -Exactly 1
            }
        }
    }

    Describe "Install-SevenZip" {
        Context "7z 9.20 is installed" {
            Mock LogTo-File { return 0 } -Verifiable
            Mock Install-Program { return 0 } -Verifiable

            $link = 'http://softlayer-ams.dl.sourceforge.net/project/' +
                    'sevenzip/7-Zip/9.20/7z920.msi'
            $hash = 'C67D3F611EA3EB3336CF92F6FFCAFDB14F8B12AF'
            $file = Join-Path $env:TEMP $link.Split('/')[-1]
            $params = @("/Q")
            $errMsg = "Failed to install 7-Zip 9.20"
            Install-SevenZip

            It "should successfully install 7z" {
                Assert-MockCalled Install-Program -Exactly 1 -ParameterFilter `
                    { ($DownloadLink -eq $link) -and
                      ($ExpectedSHA1Hash -eq $hash) -and
                      ($DestinationFile -eq $file) -and
                      ($ErrorMessage -eq $errMsg) -and
                      (((Compare-Object `
                        $params $Arguments).InputObject).Length -eq 0) }
            }

            It "should log to file" {
                Assert-MockCalled LogTo-File -Exactly 1
            }
        }
    }

    Describe "Install-SQLServerDriversForPHP" {
        Context "PHP SQL Server drivers are installed" {
            Mock LogTo-File { return 0 } -Verifiable
            Mock Install-Program { return 0 } -Verifiable
            Mock Copy-Item { return 0 } -Verifiable
            Mock Remove-Item { return 0 } -Verifiable
            $fakeExtLocation = "location"

            $link = 'http://download.microsoft.com/download/C/D/B/' +
                    'CDB0A3BB-600E-42ED-8D5E-E4630C905371/SQLSRV30.EXE'
            $hash = '1457A9F9B87119265966EEE6C9A648249A7A83E0'
            $file = Join-Path $env:TEMP $link.Split('/')[-1]
            $destination = Join-Path $env:TEMP "SQLDrivers"
            $params = @("/Q",
                        "/T:$destination",
                        "/C")
            $errMsg = "Failed to extract drivers into the specified path"
            Install-SQLServerDriversForPHP $fakeExtLocation

            It "should extract drivers" {
                Assert-MockCalled Install-Program -Exactly 1 -ParameterFilter `
                    { ($DownloadLink -eq $link) -and
                      ($ExpectedSHA1Hash -eq $hash) -and
                      ($DestinationFile -eq $file) -and
                      (((Compare-Object `
                         $params $Arguments).InputObject).Length -eq 0) -and
                        ($errMsg -eq $ErrorMessage) }
            }

            It "should copy the files" {
                Assert-MockCalled Copy-Item -Exactly 2
            }

            It "should remove temp file" {
                Assert-MockCalled Remove-Item -Exactly 1
            }

            It "should log to file" {
                Assert-MockCalled LogTo-File -Exactly 1
            }
        }
    }

    Describe "Add-PHPSettings" {
        Context "PHP settings are added" {
            Mock Set-IniFileValue { return 0 } -Verifiable

            $fakeSettings = @{'key1' = 'value1';
                              'key2' = 'value2'}
            $fakeIniPath = 'fakePath'
            Add-PHPSettings $fakeSettings "DEFAULT" $fakeIniPath

            It "should set php.ini values" {
                Assert-MockCalled Set-IniFileValue -Exactly 2
            }
        }
    }

    Describe "Enable-PHPExtensions" {
        Context "PHP extensions are enabled" {
            Mock Set-IniFileValue { return 0 } -Verifiable

            $fakeExtensions = @{'section1' = 'value1';
                                'section2' = 'value2'}
            $fakeIniPath = 'fakePath'
            Add-PHPSettings $fakeExtensions "DEFAULT" $fakeIniPath

            It "should enable php.ini extensions" {
                Assert-MockCalled Set-IniFileValue -Exactly 2
            }
        }
    }

    Describe "Configure-PHP54" {
        Context "PHP54 is configured" {
            Mock Copy-Item { return 0 } -Verifiable
            Mock Set-IniFileValue { return 0 } -Verifiable
            Mock Add-PHPSettings { return 0 } -Verifiable
            Mock Enable-PHPExtensions { return 0 } -Verifiable
            Mock Execute-Command { return 0 } -Verifiable
            Mock LogTo-File { return 0 } -Verifiable
            $fakePHPLocation = 'location1'
            $fakeExtLocation = 'location2'

            Configure-PHP54 -PHPLocation $fakePHPLocation `
                            -ExtLocation $fakeExtLocation

            It "should create php.ini file" {
                Assert-MockCalled Copy-Item -Exactly 1
            }

            It "should set php memory limit" {
                Assert-MockCalled Set-IniFileValue -Exactly 1
            }

            It "should add desired php settings" {
                Assert-MockCalled Add-PHPSettings -Exactly 1
            }

            It "should enable php extensions" {
                Assert-MockCalled Enable-PHPExtensions -Exactly 1
            }

            It "should configure IIS for PHP" {
                Assert-MockCalled Execute-Command -Exactly 4
            }

            It "should log to file" {
                Assert-MockCalled LogTo-File -Exactly 1
            }
        }
    }

    Describe "Install-PHP54" {
        Context "PHP54 is installed" {
            Mock New-Item { return 0 } -Verifiable
            Mock Download-File { return 0 } -Verifiable
            Mock Check-FileIntegrityWithSHA1 { return 0 } -Verifiable
            Mock Unzip-File { return 0 } -Verifiable
            Mock Remove-Item { return 0 } -Verifiable
            Mock Install-SQLServerDriversForPHP { return 0 } -Verifiable
            Mock Configure-PHP54 { return 0 } -Verifiable
            Mock LogTo-File { return 0 } -Verifiable
            $fakePHPLocation = "location"

            Install-PHP54 $fakePHPLocation

            It "should create new folder for PHP" {
                Assert-MockCalled New-Item -Exactly 1 `
                    -ParameterFilter { $ItemType -eq "Directory" }
            }

            It "should download PHP54" {
                Assert-MockCalled Download-File -Exactly 1
            }

            It "should check file integrity" {
                Assert-MockCalled Check-FileIntegrityWithSHA1 -Exactly 1
            }

            It "should unzip PHP 5.4" {
                Assert-MockCalled Unzip-File -Exactly 1
            }

            It "should remove temporary file" {
                Assert-MockCalled Remove-Item -Exactly 1
            }

            It "should install sql server drivers for PHP" {
                Assert-MockCalled Install-SQLServerDriversForPHP -Exactly 1
            }

            It "should configure PHP 5.4" {
                Assert-MockCalled Configure-PHP54 -Exactly 1
            }

            It "should log to file" {
                Assert-MockCalled LogTo-File -Exactly 1
            }
        }
    }

    Describe "Install-Drupal7" {
        Context "Drupal7 is installed" {
            Mock Install-Program { return 0 } -Verifiable
            Mock Download-File { return 0 } -Verifiable
            Mock Check-FileIntegrityWithSHA1 { return 0 } -Verifiable
            Mock Unzip-File { return 0 } -Verifiable
            Mock New-Item { return 0 } -Verifiable
            Mock Copy-Item { return 0 } -Verifiable
            Mock Remove-Item { return 0 } -Verifiable
            Mock Execute-Command { return 0 } -Verifiable
            Mock Push-Location { return 0 } -Verifiable
            Mock Pop-Location { return 0 } -Verifiable
            Mock LogTo-File { return 0 } -Verifiable

            $fakeSAPassword = "password"
            $fakeAdminUsername = "admin"
            $fakeAdminPassword = "password"
            $fakeAdminEmail = "admin@admim.com"
            $fakeWebsiteName = "website"
            Install-Drupal7 $fakeSAPassword `
                            $fakeAdminUsername `
                            $fakeAdminPassword `
                            $fakeAdminEmail `
                            $fakeWebsiteName

            It "should install every required program" {
                Assert-MockCalled Install-Program -Exactly 4
            }

            It "should download every file" {
                Assert-MockCalled Download-File -Exactly 2
            }

            It "should copy files" {
                Assert-MockCalled Copy-Item -Exactly 3
            }

            It "should create new folders" {
                Assert-MockCalled New-Item -Exactly 2 `
                    -ParameterFilter { $ItemType -eq "Directory" }
            }

            It "should check files for integrity" {
                Assert-MockCalled Check-FileIntegrityWithSHA1 -Exactly 2
            }

            It "should unzip downloaded zip files" {
                Assert-MockCalled Unzip-File -Exactly 2
            }

            It "should remove temporary files" {
                Assert-MockCalled Remove-Item -Exactly 3
            }

            It "should execute configuration commands" {
                Assert-MockCalled Execute-Command -Exactly 9
            }

            It "should Push-Location to Drupal web site location" {
                Assert-MockCalled Push-Location -Exactly 1
            }

            It "should go to the previous location" {
                Assert-MockCalled Pop-Location -Exactly 1
            }

            It "should log to file" {
                Assert-MockCalled LogTo-File -Exactly 3
            }
        }
    }

    Describe "Install-IISWithDrupal" {
        Context "Drupal7 on IIS is installed" {
            Mock Install-IIS { return 0 } -Verifiable
            Mock Install-SQLServerExpress2008R2SP2 { return 0 } -Verifiable
            Mock Install-SevenZip { return 0 } -Verifiable
            Mock Install-PHP54 { return 0 } -Verifiable
            Mock Install-Drupal7 { return 0 } -Verifiable

            $fakeParams = @{
                'ENDPOINT'    = 'token';
                'TOKEN'       = 'endpoint';
                'SA_PASS'     = 'password';
                'ADMIN_USER'  = 'user';
                'ADMIN_PASS'  = "password";
                'ADMIN_EMAIL' = 'email';
                'SITE_NAME'   = "website"
            }
            $phpLoc = Join-Path $env:SystemDrive "PHP\PHP54"
            Install-IISWithDrupal $fakeParams

            It "should install IIS" {
                Assert-MockCalled Install-IIS -Exactly 1
            }

            It "should install SQLServerExpress2008R2SP2" {
                Assert-MockCalled Install-SQLServerExpress2008R2SP2 -Exactly 1 `
                    -ParameterFilter {
                        $SAPassword -eq $fakeParams['SA_PASS']
                    }
            }

            It "should install SevenZip" {
                Assert-MockCalled Install-SevenZip -Exactly 1
            }

            It "should install PHP54" {
                Assert-MockCalled Install-PHP54 -Exactly 1 `
                    -ParameterFilter {
                        $PHPLocation -eq $phpLoc
                    }
            }

            It "should install Drupal7" {
                Assert-MockCalled Install-Drupal7 -Exactly 1 `
                    -ParameterFilter {
                        ($SAPassword -eq $fakeParams['SA_PASS']) -and
                        ($AdminUsername -eq $fakeParams['ADMIN_USER']) -and
                        ($AdminPassword -eq $fakeParams['ADMIN_PASS']) -and
                        ($AdminEmail -eq $fakeParams['ADMIN_EMAIL']) -and
                        ($WebsiteName -eq $fakeParams['SITE_NAME'])
                    }
            }
        }
    }

    Describe "Initialize-Server" {
        Mock LogTo-File { return 0 } -Verifiable
        Mock Send-HeatWaitSignal { return 0 } -Verifiable
        $fakeParams = @{
            'ENDPOINT'    = 'token';
            'TOKEN'       = 'endpoint';
            'SA_PASS'     = 'password';
            'ADMIN_USER'  = 'user';
            'ADMIN_PASS'  = "password";
            'ADMIN_EMAIL' = 'email';
            'SITE_NAME'   = "website"
        }

        Context "Successful initialization" {
            Mock Install-IISWithDrupal { return 0 } -Verifiable

            Initialize-Server $fakeParams

            It "should log to file" {
                Assert-MockCalled LogTo-File -Exactly 2 -Scope Context
            }

            It "should install IIS with Drupal" {
                Assert-MockCalled Install-IISWithDrupal -Exactly 1 `
                                                        -Scope Context
            }

            It "should send heat wait signal" {
                Assert-MockCalled Send-HeatWaitSignal -Exactly 1 `
                                                      -Scope Context
            }
        }

        Context "Unsuccessful initialization" {
            Mock Install-IISWithDrupal { throw } -Verifiable

            Initialize-Server $fakeParams

            It "should log to file" {
                Assert-MockCalled LogTo-File -Exactly 3 -Scope Context
            }

            It "should install IIS with Drupal" {
                Assert-MockCalled Install-IISWithDrupal -Exactly 1 `
                                                        -Scope Context
            }

            It "should send heat wait signal" {
                Assert-MockCalled Send-HeatWaitSignal -Exactly 1 `
                                                      -Scope Context
            }
        }
    }
}

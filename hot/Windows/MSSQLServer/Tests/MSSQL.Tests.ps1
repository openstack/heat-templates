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

$moduleName = "MSSQL"
$modulePath = "../MSSQL.psm1"

$currentLocation = Split-Path -Parent $MyInvocation.MyCommand.Path
$fullPath = Join-Path $currentLocation $modulePath

Remove-Module -Name $moduleName -ErrorAction SilentlyContinue
Import-Module -Name $fullPath -DisableNameChecking -Force

InModuleScope $moduleName {
    Describe "Test Add MSSQL User" {
        Context "On success" {
            Mock Log { return $true } -Verifiable
            Mock Add-WindowsUser { return $true } -Verifiable

            Add-MSSQLUser "fakeuser" "fakepassword"

            It "should verify caled all mocks" {
                Assert-VerifiableMocks
            }
        }
    }
}

InModuleScope $moduleName {
    Describe "Test Add Net Rules" {
        Context "On success" {
            Mock netsh.exe { return $true } -Verifiable
            Mock New-NetFirewallRule { return $true } -Verifiable

            Add-NetRules

            It "should verify caled all mocks" {
                Assert-VerifiableMocks
            }
        }
    }
}

InModuleScope $moduleName {
    Describe "Test Get MSSQLLogFile" {
        Context "On Success" {
            $MSSQLVersion = "13"
            Mock Join-Path { return $true } -Verifiable

            Get-MSSQLLogFile $MSSQLVersion

            It "should verify caled all mocks" {
                Assert-VerifiableMocks
            }
        }
    }
}

InModuleScope $moduleName {
    Describe "Test Get MSSQLVersion" {
        Context "On Success" {
            $MSSQLVersion = "13"
            Mock Load-XML { return $MSSQLVersion } -Verifiable
            Mock Log { return $true} -Verifiable
            $version =Get-MSSQLVersion $MSSQLVersion

            It "should verify caled all mocks" {
                Assert-VerifiableMocks
            }
        }
    }
}


InModuleScope $moduleName {
    Describe "Test Get MSSQL Error" {
    $sqlLogFile = Join-Path ${ENV:ProgramFiles} -ChildPath `
"\Microsoft SQL Server\110\Setup Bootstrap\Log\Summary.txt"
        Context "With errors" {
            $fakeErrors = @("err1")

            Mock Select-String { return $fakeErrors } -Verifiable
            Mock Log { return $true } -Verifiable

            $result = Get-MSSQLError

            It "should return true" {
                $result | Should Be $true
            }

            It "should verify caled all mocks" {
                Assert-VerifiableMocks
            }
        }
        Context "No errors" {
            $fakeErrors = @()

            Mock Select-String { return $fakeErrors } -Verifiable

            $result = Get-MSSQLError

            It "should return false" {
                $result | Should Be $false
            }

            It "should verify caled all mocks" {
                Assert-VerifiableMocks
            }
        }
    }
}

InModuleScope $moduleName {
    Describe "Test Install Required Features" {
        Context "No reboot" {
            $fakeStatus = @{"Reboot"=$false}
            Mock Install-WindowsFeatures { return $fakeStatus } -Verifiable

            Install-RequiredFeatures

            It "should verify caled all mocks" {
                Assert-VerifiableMocks
            }
        }
        Context "With reboot" {
            $fakeStatus = @{"Reboot"=$true}
            Mock Install-WindowsFeatures { return $fakeStatus } -Verifiable
            Mock ExitFrom-Script { return $true } -Verifiable
            Mock Log { return $true } -Verifiable

            Install-RequiredFeatures

            It "should verify caled all mocks" {
                Assert-VerifiableMocks
            }
        }
    }
}

InModuleScope $moduleName {
    Describe "Test Install internal MSSQL" {
        $mssqlServiceUsername="mssql-service-username";
        $mssqlServicePassword = "mssql-service-user-password";
        $mssqlSaPassword = "mssql-sa-password";
        $mssqlFeatures = "mssql-features";
        $mssqlInstanceName = "mssql-instance-name";
        $mssqlIsoUNCPath = "mssql_iso_unc_path";
        $mssqlWaitConditionEndpoint = "mssql_wait_condition_endpoint";
        $mssqlWaitConditionToken = "mssql_wait_condition_token";
        Context "On success" {

            $cimInstance = New-CimInstance -ClassName "MSFT_DiskImage" `
                             -Namespace "root/Microsoft/Windows/Storage" `
                             -ClientOnly `
                             -Property @{"ImagePath"="fakePath"}

            Mock Log { return $true } -Verifiable
            Mock Install-RequiredFeatures { return $true } -Verifiable
            Mock Add-MsSQLUser { return $true } -Verifiable
            Mock Copy-FilesLocal { return $true } -Verifiable
            Mock Mount-DiskImage { return $cimInstance } -Verifiable
            Mock Get-Volume { return $true } -Verifiable
            Mock Get-MSSQLVersion { return $MediaInfoXMLPath } -Verifiable
            Mock Get-MSSQLLogFile { return $MSSQLVersion } -Verifiable
            Mock Test-Path { return $true } -Verifiable
            Mock Remove-Item { return $true } -Verifiable
            Mock Get-MSSQLParameters { return $true } -Verifiable
            Mock ExecuteWith-Retry { return $true } -Verifiable
            Mock Dismount-DiskImage { return $true } -Verifiable
            Mock Get-MssqlError { return $false } -Verifiable
            Mock Add-NetRules { return $true } -Verifiable
            Mock Send-HeatWaitSignal { return $true } -Verifiable

            $result = Install-MSSQLInternal -MssqlServiceUsername $mssqlServiceUsername `
                        -MssqlServicePassword $mssqlServicePassword `
                        -MssqlSaPassword $mssqlSaPassword `
                        -MssqlFeatures $mssqlFeatures `
                        -MssqlInstanceName $mssqlInstanceName `
                        -MssqlIsoUNCPath $mssqlIsoUNCPath `
                        -MssqlWaitConditionEndpoint $mssqlWaitConditionEndpoint `
                        -MssqlWaitConditionToken $MssqlWaitConditionToken

            It "should succeed" {
                $result | Should Be $true
            }

            It "should verify caled all mocks" {
                Assert-VerifiableMocks
            }
        }

        Context "On failure internal" {

            Mock Install-MSSQLInternal { throw } -Verifiable
            Mock Log { return $true } -Verifiable
            Mock Send-HeatWaitSignal { return $true } -Verifiable

            Install-MSSQL -MssqlServiceUsername $mssqlServiceUsername `
                        -MssqlServicePassword $mssqlServicePassword `
                        -MssqlSaPassword $mssqlSaPassword `
                        -MssqlFeatures $mssqlFeatures `
                        -MssqlInstanceName $mssqlInstanceName `
                        -MssqlIsoUNCPath $mssqlIsoUNCPath `
                        -MssqlWaitConditionEndpoint $mssqlWaitConditionEndpoint `
                        -MssqlWaitConditionToken $MssqlWaitConditionToken

            It "should verify caled all mocks" {
                Assert-VerifiableMocks
            }
        }

        Context "On succes internal" {

            Mock Install-MSSQLInternal { return $true } -Verifiable

            $result = Install-MSSQL -MssqlServiceUsername $mssqlServiceUsername `
                        -MssqlServicePassword $mssqlServicePassword `
                        -MssqlSaPassword $mssqlSaPassword `
                        -MssqlFeatures $mssqlFeatures `
                        -MssqlInstanceName $mssqlInstanceName `
                        -MssqlIsoUNCPath $mssqlIsoUNCPath `
                        -MssqlWaitConditionEndpoint $mssqlWaitConditionEndpoint `
                        -MssqlWaitConditionToken $MssqlWaitConditionToken

            It "should be successful" {
                $result | Should Be $true
            }

            It "should verify caled all mocks" {
                Assert-VerifiableMocks
            }
        }
    }
}

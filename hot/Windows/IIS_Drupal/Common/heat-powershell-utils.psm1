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

$rebotCode = 1001
$reexecuteCode = 1002
$rebootAndReexecuteCode = 1003

function ExitFrom-Script {
    param(
        [int]$ExitCode
    )

    exit $ExitCode
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

function Execute-Command {
    param(
        [ScriptBlock]$Command,
        [array]$Arguments=@(),
        [string]$ErrorMessage
    )

    $res = Invoke-Command -ScriptBlock $Command -ArgumentList $Arguments
    if ($LASTEXITCODE -ne 0) {
        throw $ErrorMessage
    }
    return $res
}

function Is-WindowsServer2008R2 () {
    $winVer = (Get-WmiObject -class Win32_OperatingSystem).Version.Split('.')
    return (($winVer[0] -eq 6) -and ($winVer[1] -eq 1))
}

function Get-PSMajorVersion () {
    return $PSVersionTable.PSVersion.Major
}

function Install-WindowsFeatures {
     param(
        [Parameter(Mandatory=$true)]
        [array]$Features,
        [int]$RebootCode=$rebootAndReexecuteCode
    )

    if ((Is-WindowsServer2008R2) -eq $true) {
        Import-Module ServerManager
    }

    $rebootNeeded = $false
    foreach ($feature in $Features) {
        if ((Is-WindowsServer2008R2) -eq $true) {
            $state = ExecuteWith-Retry -Command {
                Add-WindowsFeature -Name $feature -ErrorAction Stop
            }
        } else {
            $state = ExecuteWith-Retry -Command {
                Install-WindowsFeature -Name $feature -ErrorAction Stop
            }
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
        ExitFrom-Script $RebootCode
    }
}

function Unzip-File {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ZipFile,
        [Parameter(Mandatory=$true)]
        [string]$Destination,
        [string]$7zPath = "${env:ProgramFiles(x86)}\7-Zip\7z.exe"
    )

    $res = Execute-Command -Command {
        & $7zPath x "-o$Destination" $ZipFile
    }
    return $res
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
    }
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
        $f = [System.IO.File]::OpenRead($fullPath)
        $sham = $null
        try {
            $sham = New-Object System.Security.Cryptography.SHA1Managed
            $hash = $sham.ComputeHash($f)
            $hashSB = New-Object System.Text.StringBuilder `
                                -ArgumentList ($hash.Length * 2)
            foreach ($b in $hash) {
                $sb = $hashSB.AppendFormat("{0:x2}", $b)
            }
            return [PSCustomObject]@{ Algorithm="SHA1";
                                      Hash=$hashSB.ToString().ToUpper();
                                      Path=$fullPath }
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
        [Parameter(Mandatory=$true)]
        [array]$Arguments,
        [Parameter(Mandatory=$true)]
        [string]$ErrorMessage
    )

    Download-File $DownloadLink $DestinationFile
    Check-FileIntegrityWithSHA1 $DestinationFile $ExpectedSHA1Hash

    $p = Start-Process -FilePath $DestinationFile `
                       -ArgumentList $Arguments `
                       -PassThru `
                       -Wait
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
        $retVal = [PSCloudbase.Win32IniApi]::WritePrivateProfileString($Section, $Key, $Value, $Path)
        if (!$retVal -and [PSCloudbase.Win32IniApi]::GetLastError()) {
            throw "Cannot set value in ini file: " + [PSCloudbase.Win32IniApi]::GetLastError()
        }
    }
}

# Invoke-RestMethod for Powershell versions less than 4.0
function Invoke-RestMethodWrapper {
    param(
        [Uri]$Uri,
        [Object]$Body,
        [System.Collections.IDictionary]$Headers,
        [string]$Method
    )

    $request = [System.Net.WebRequest]::Create($Uri)
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
        $encoding = [System.Text.Encoding]::GetEncoding("iso-8859-1")
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
        [Uri]$Endpoint,
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

    $status = $statusMap[$Success]
    $heatMessageJSON =
    "{
        `"status`":  `"$status`",
        `"reason`":  `"Configuration script has been executed.`",
        `"data`":  `"$Message`"
    }"

    $headers = @{
        "X-Auth-Token"=$Token;
        "Accept"="application/json";
        "Content-Type"= "application/json";
    }

    Invoke-HeatRestMethod -Endpoint $Endpoint `
                          -HeatMessageJSON $heatMessageJSON `
                          -Headers $headers
}

function LogTo-File {
    param(
        $LogMessage,
        $LogFile="C:\cfn\userdata.log",
        $Topic="General"
    )

    $date = Get-Date
    $fullMessage = "$date | $Topic | $LogMessage"
    Add-Content -Path $LogFile -Value $fullMessage
}

Export-ModuleMember -Function *

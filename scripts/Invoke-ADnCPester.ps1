#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(5, 7)]
    [int]$ExpectedMajor,

    [string]$ResultsDirectory = (Join-Path $PSScriptRoot '..\test-results')
)

$ErrorActionPreference = 'Stop'

# Protect the test contract: this CI job must run on Windows in the requested engine.
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw 'The AD&C PowerShell CI test requires Windows.'
}
if ($PSVersionTable.PSVersion.Major -ne $ExpectedMajor) {
    throw "Wrong PowerShell major version: expected $ExpectedMajor, actual $($PSVersionTable.PSVersion)."
}

$requiredPester = '5.7.1'
$loaded = Import-Module Pester -RequiredVersion $requiredPester -Force -PassThru -ErrorAction Stop
if ($loaded.Version.ToString() -ne $requiredPester) {
    throw "Pester version mismatch: expected $requiredPester, actual $($loaded.Version)."
}

$testDirectory = Join-Path $PSScriptRoot '..\tests\powershell'
if (-not (Test-Path -LiteralPath $testDirectory -PathType Container)) {
    throw "Test directory not found: $testDirectory"
}
$testFiles = @(Get-ChildItem -LiteralPath $testDirectory -Filter '*.Tests.ps1' -File)
if ($testFiles.Count -eq 0) {
    throw 'No *.Tests.ps1 files found. Refusing an empty green test run.'
}

$null = New-Item -Path $ResultsDirectory -ItemType Directory -Force
$reportPath = Join-Path (Resolve-Path -LiteralPath $ResultsDirectory).Path "pester-ps$ExpectedMajor.xml"

$config = New-PesterConfiguration
$config.Run.Path = @($testDirectory)
$config.Run.PassThru = $true
$config.Output.Verbosity = 'Detailed'
$config.TestResult.Enabled = $true
$config.TestResult.OutputFormat = 'NUnitXml'
$config.TestResult.OutputPath = $reportPath

Write-Host "PowerShell: $($PSVersionTable.PSVersion); Pester: $requiredPester"
Write-Host "Tests: $testDirectory"
$result = Invoke-Pester -Configuration $config
if ($null -eq $result) {
    throw 'Pester returned no summary.'
}
Write-Host "Tests: total=$($result.TotalCount), passed=$($result.PassedCount), failed=$($result.FailedCount), skipped=$($result.SkippedCount)"
if ($result.TotalCount -lt 1 -or $result.FailedCount -gt 0) {
    throw 'Pester tests failed or no tests were executed.'
}
if (-not (Test-Path -LiteralPath $reportPath -PathType Leaf)) {
    throw "Pester did not produce NUnit XML: $reportPath"
}
Write-Host "PASS: $reportPath"

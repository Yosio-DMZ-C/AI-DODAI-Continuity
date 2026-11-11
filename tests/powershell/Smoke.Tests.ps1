# This file tests the CI harness only. It does not claim to test AD&C production scripts.
Describe 'AD&C Windows PowerShell test harness' {
    It 'runs on Windows' {
        [Environment]::OSVersion.Platform.ToString() | Should -Be 'Win32NT'
    }

    It 'uses a supported PowerShell major version' {
        $PSVersionTable.PSVersion.Major | Should -BeIn @(5, 7)
    }

    It 'round-trips Japanese text through an isolated temporary file' {
        $path = Join-Path $TestDrive 'unicode.txt'
        Set-Content -LiteralPath $path -Value 'AD&C 日本語テスト' -Encoding UTF8
        (Get-Content -LiteralPath $path -Encoding UTF8) | Should -Be 'AD&C 日本語テスト'
    }

    It 'detects a deliberately thrown error' {
        { throw 'expected test-only failure' } | Should -Throw
    }
}

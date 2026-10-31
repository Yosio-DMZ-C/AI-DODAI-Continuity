# Synthetic, temporary data only. Never touches real users' work files.
BeforeAll {
    $script:archiver = Join-Path $PSScriptRoot '..\..\scripts\Export-UserWorkArchive.ps1'
    Add-Type -AssemblyName System.IO.Compression -ErrorAction Stop
    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop
}
Describe 'Export-UserWorkArchive (local backup / no security bypass)' {
    BeforeEach {
        # Pester's TestDrive is shared within Describe; use a fresh case folder.
        $caseRoot = Join-Path $TestDrive ([guid]::NewGuid().ToString('N'))
        $null = New-Item -Path $caseRoot -ItemType Directory
        $script:source = Join-Path $caseRoot 'source'
        $script:destination = Join-Path $caseRoot 'backup.zip'
        $null = New-Item -Path $script:source -ItemType Directory
    }

    It 'supports preview mode without creating a ZIP' {
        Set-Content -LiteralPath (Join-Path $script:source 'sample.bat') -Value '@echo off'
        $result = & $script:archiver -SourceDirectory $script:source -DestinationZip $script:destination -DryRun
        $result.DryRun | Should -BeTrue
        $result.FileCount | Should -Be 1
        (Test-Path -LiteralPath $script:destination) | Should -BeFalse
    }

    It 'stores allowed script, text and Office extensions but excludes executables' {
        Set-Content -LiteralPath (Join-Path $script:source 'command.bat') -Value 'echo synthetic'
        Set-Content -LiteralPath (Join-Path $script:source 'readme.txt') -Value 'synthetic'
        Set-Content -LiteralPath (Join-Path $script:source 'document.docx') -Value 'dummy Office fixture'
        Set-Content -LiteralPath (Join-Path $script:source 'skip.exe') -Value 'not an executable'
        $result = & $script:archiver -SourceDirectory $script:source -DestinationZip $script:destination
        $result.FileCount | Should -Be 3
        $zip = [IO.Compression.ZipFile]::OpenRead($script:destination)
        try {
            $names = @($zip.Entries | ForEach-Object { $_.FullName })
            $names.Count | Should -Be 3
            $names | Should -Contain 'command.bat'
            $names | Should -Contain 'readme.txt'
            $names | Should -Contain 'document.docx'
            $names | Should -Not -Contain 'skip.exe'
        } finally { $zip.Dispose() }
    }

    It 'leaves original files untouched' {
        $path = Join-Path $script:source 'owner.txt'
        [IO.File]::WriteAllText($path,'unchanged test content')
        $before = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
        $null = & $script:archiver -SourceDirectory $script:source -DestinationZip $script:destination
        (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash | Should -Be $before
    }

    It 'does not descend into subdirectories unless Recurse is specified' {
        Set-Content -LiteralPath (Join-Path $script:source 'root.txt') -Value 'root'
        $nested = Join-Path $script:source 'nested'
        $null = New-Item -Path $nested -ItemType Directory
        Set-Content -LiteralPath (Join-Path $nested 'inner.xlsx') -Value 'synthetic'
        $result = & $script:archiver -SourceDirectory $script:source -DestinationZip $script:destination
        $result.FileCount | Should -Be 1
    }

    It 'preserves relative paths when recursion is enabled' {
        $nested = Join-Path $script:source 'nested'
        $null = New-Item -Path $nested -ItemType Directory
        Set-Content -LiteralPath (Join-Path $nested 'inner.xlsx') -Value 'synthetic'
        $result = & $script:archiver -SourceDirectory $script:source -DestinationZip $script:destination -Recurse
        $result.FileCount | Should -Be 1
        $zip = [IO.Compression.ZipFile]::OpenRead($script:destination)
        try {
            @($zip.Entries | ForEach-Object { $_.FullName }) | Should -Contain 'nested/inner.xlsx'
        } finally { $zip.Dispose() }
    }

    It 'ignores hidden files even if the extension is allowed' {
        Set-Content -LiteralPath (Join-Path $script:source 'visible.txt') -Value 'visible'
        $hidden = Join-Path $script:source 'hidden.txt'
        Set-Content -LiteralPath $hidden -Value 'hidden'
        [IO.File]::SetAttributes($hidden, [IO.FileAttributes]::Hidden)
        $result = & $script:archiver -SourceDirectory $script:source -DestinationZip $script:destination -DryRun
        $result.FileCount | Should -Be 1
    }

    It 'does not replace a pre-existing destination' {
        Set-Content -LiteralPath (Join-Path $script:source 'file.txt') -Value 'source'
        Set-Content -LiteralPath $script:destination -Value 'existing backup'
        { & $script:archiver -SourceDirectory $script:source -DestinationZip $script:destination } | Should -Throw
        (Get-Content -LiteralPath $script:destination -Raw) | Should -Match 'existing backup'
    }

    It 'rejects writing the output into the source folder' {
        Set-Content -LiteralPath (Join-Path $script:source 'file.txt') -Value 'source'
        $bad = Join-Path $script:source 'inside.zip'
        { & $script:archiver -SourceDirectory $script:source -DestinationZip $bad } | Should -Throw
        (Test-Path -LiteralPath $bad) | Should -BeFalse
    }

    It 'rejects missing source folders' {
        $missing = Join-Path $TestDrive 'not-present'
        { & $script:archiver -SourceDirectory $missing -DestinationZip $script:destination } | Should -Throw
    }

    It 'rejects an empty set of eligible files' {
        Set-Content -LiteralPath (Join-Path $script:source 'binary.exe') -Value 'not selected'
        { & $script:archiver -SourceDirectory $script:source -DestinationZip $script:destination } | Should -Throw
        (Test-Path -LiteralPath $script:destination) | Should -BeFalse
    }

    It 'enforces a maximum number of files' {
        Set-Content -LiteralPath (Join-Path $script:source 'a.txt') -Value 'a'
        Set-Content -LiteralPath (Join-Path $script:source 'b.txt') -Value 'b'
        { & $script:archiver -SourceDirectory $script:source -DestinationZip $script:destination -MaxFiles 1 } | Should -Throw
        (Test-Path -LiteralPath $script:destination) | Should -BeFalse
    }

    It 'enforces a total size limit before archiving' {
        $large = Join-Path $script:source 'large.txt'
        [IO.File]::WriteAllBytes($large, (New-Object byte[] (1048577)))
        { & $script:archiver -SourceDirectory $script:source -DestinationZip $script:destination -MaxTotalMB 1 } | Should -Throw
        (Test-Path -LiteralPath $script:destination) | Should -BeFalse
    }

    It 'prevents archiving a volume root' {
        $driveRoot = [IO.Path]::GetPathRoot($script:source)
        { & $script:archiver -SourceDirectory $driveRoot -DestinationZip $script:destination -DryRun } | Should -Throw
    }

    It 'does not enter the excluded .git directory' {
        $gitDir = Join-Path $script:source '.git'
        $null = New-Item -Path $gitDir -ItemType Directory
        Set-Content -LiteralPath (Join-Path $gitDir 'config.txt') -Value 'config'
        Set-Content -LiteralPath (Join-Path $script:source 'owner.md') -Value 'work'
        $result = & $script:archiver -SourceDirectory $script:source -DestinationZip $script:destination -Recurse -DryRun
        $result.FileCount | Should -Be 1
    }
}

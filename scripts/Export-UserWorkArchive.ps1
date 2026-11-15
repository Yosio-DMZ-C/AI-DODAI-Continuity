#Requires -Version 5.1
<#
.SYNOPSIS
  Creates a local ZIP of explicitly selected document and text/script file types.
.DESCRIPTION
  Transparent, user-initiated archival. Never executes source files, reads nothing
  outside SourceDirectory, uses no network, encryption or security-control bypass.
  Hidden/system items and reparse points are excluded. Existing ZIPs are not replaced.
  Preview is the default; writing a ZIP requires explicit -CreateArchive.
  Default scope is 200 files or 100 MB; no recursion unless requested.
  Output must be in an existing directory outside the source tree.
.EXAMPLE
  .\Export-UserWorkArchive.ps1 -SourceDirectory 'C:\Work\ProjectA' -DestinationZip 'C:\Backups\ProjectA.zip' -Recurse -DryRun
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$SourceDirectory,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$DestinationZip,

    [switch]$Recurse,
    [switch]$DryRun,
    [switch]$CreateArchive,

    [ValidateRange(1,5000)]
    [int]$MaxFiles = 200,

    [ValidateRange(1,10240)]
    [int]$MaxTotalMB = 100
)

$ErrorActionPreference = 'Stop'
if ($DryRun -and $CreateArchive) {
    throw 'Specify -DryRun (preview) or -CreateArchive (write), not both.'
}
$allowedExtensions = @(
    '.bat','.cmd','.ps1','.txt','.md','.csv','.rtf',
    '.doc','.docx','.xls','.xlsx','.ppt','.pptx','.odt','.ods','.odp'
)

if (-not (Test-Path -LiteralPath $SourceDirectory -PathType Container)) {
    throw "Source directory does not exist: $SourceDirectory"
}
$sourceItem = Get-Item -LiteralPath $SourceDirectory -Force
if (($sourceItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'Source directory must not be a link or reparse point.'
}
$source = [IO.Path]::GetFullPath($sourceItem.FullName).TrimEnd([char[]]@('\','/'))
$root = [IO.Path]::GetPathRoot($source).TrimEnd([char[]]@('\','/'))
if ([string]::Equals($source, $root, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'A drive or share root is not an allowed source scope.'
}
if ($source.StartsWith('\\')) {
    throw 'Network source paths are not supported.'
}
if (-not [IO.Path]::IsPathRooted($DestinationZip)) {
    throw 'DestinationZip must be an absolute path.'
}
$destination = [IO.Path]::GetFullPath($DestinationZip)
if (-not [string]::Equals([IO.Path]::GetExtension($destination), '.zip', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'DestinationZip must have a .zip extension.'
}
if ($destination.StartsWith('\\')) {
    throw 'Network destination paths are not supported.'
}
if ($destination.StartsWith(($source + [IO.Path]::DirectorySeparatorChar), [StringComparison]::OrdinalIgnoreCase)) {
    throw 'DestinationZip must be outside SourceDirectory.'
}
$destinationParent = [IO.Path]::GetDirectoryName($destination)
if (-not [IO.Directory]::Exists($destinationParent)) {
    throw "Destination parent directory does not exist: $destinationParent"
}
if (([IO.File]::GetAttributes($destinationParent) -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'Destination directory must not be a link or reparse point.'
}
if ([IO.File]::Exists($destination)) {
    throw "Destination already exists; refusing to overwrite: $destination"
}

$folders = New-Object 'System.Collections.Generic.Queue[string]'
$folders.Enqueue($source)
$selected = New-Object 'System.Collections.Generic.List[System.IO.FileInfo]'
[long]$bytes = 0
[long]$maximumBytes = [long]$MaxTotalMB * 1MB

while ($folders.Count -gt 0) {
    $directory = $folders.Dequeue()
    foreach ($item in @(Get-ChildItem -LiteralPath $directory -Force -ErrorAction Stop)) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
            ($item.Attributes -band [IO.FileAttributes]::Hidden) -ne 0 -or
            ($item.Attributes -band [IO.FileAttributes]::System) -ne 0) {
            continue
        }
        if ($item.PSIsContainer) {
            if ($Recurse -and $item.Name -notin @('.git','.svn','node_modules','AppData')) {
                $folders.Enqueue($item.FullName)
            }
            continue
        }
        if ($item.Extension.ToLowerInvariant() -notin $allowedExtensions) {
            continue
        }
        if ($selected.Count -ge $MaxFiles) {
            throw "File count exceeds MaxFiles ($MaxFiles)."
        }
        $bytes += $item.Length
        if ($bytes -gt $maximumBytes) {
            throw "Selected files exceed MaxTotalMB ($MaxTotalMB MB)."
        }
        $selected.Add([IO.FileInfo]$item)
    }
}

if ($selected.Count -eq 0) {
    throw 'No matching files found; no ZIP created.'
}

$report = [pscustomobject]@{
    SourceDirectory = $source
    ArchivePath     = $destination
    FileCount       = $selected.Count
    TotalBytes      = $bytes
    SelectedFiles   = @($selected | Sort-Object FullName | ForEach-Object {
        $_.FullName.Substring($source.Length).TrimStart([char[]]@('\','/')).Replace('\','/')
    })
    DryRun          = -not [bool]$CreateArchive
}
if (-not $CreateArchive) {
    return $report
}

Add-Type -AssemblyName System.IO.Compression -ErrorAction Stop
Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop
$temporaryZip = Join-Path $destinationParent ('.adnc-archive-' + [guid]::NewGuid().ToString('N') + '.partial')
$archive = $null
try {
    $archive = [IO.Compression.ZipFile]::Open($temporaryZip, [IO.Compression.ZipArchiveMode]::Create)
    foreach ($file in ($selected | Sort-Object FullName)) {
        $relativeName = $file.FullName.Substring($source.Length).TrimStart([char[]]@('\','/')).Replace('\','/')
        $null = [IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $archive, $file.FullName, $relativeName, [IO.Compression.CompressionLevel]::NoCompression)
    }
    $archive.Dispose()
    $archive = $null
    [IO.File]::Move($temporaryZip, $destination)
}
finally {
    if ($null -ne $archive) { $archive.Dispose() }
    if ([IO.File]::Exists($temporaryZip)) { [IO.File]::Delete($temporaryZip) }
}
return $report

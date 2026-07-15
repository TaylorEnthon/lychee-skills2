param([string]$ClaudeHome = "$env:USERPROFILE\.claude")

$ErrorActionPreference = "Stop"
$SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Name = Split-Path -Leaf $SourceDir
$Target = Join-Path $ClaudeHome "skills\$Name"
$RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $SourceDir "..\.."))
$Shared = Join-Path $RepoRoot "shared"

foreach ($Path in @("SKILL.md", "doctor.sh", "doctor.ps1", "install.sh", "install.ps1", "scripts", "references", "data")) {
    $FullPath = Join-Path $SourceDir $Path
    if (-not (Test-Path -LiteralPath $FullPath)) { throw "Required source path is missing: $FullPath" }
}
if (-not (Test-Path -LiteralPath $Shared)) { throw "Required source path is missing: $Shared" }

foreach ($Path in @("scripts", "shared", "references", "data")) {
    $FullPath = Join-Path $Target $Path
    if (Test-Path -LiteralPath $FullPath) { Remove-Item -LiteralPath $FullPath -Recurse -Force }
}
New-Item -ItemType Directory -Path $Target -Force | Out-Null
foreach ($Path in @("SKILL.md", "doctor.sh", "doctor.ps1", "install.sh", "install.ps1")) {
    Copy-Item -LiteralPath (Join-Path $SourceDir $Path) -Destination $Target -Force
}
Copy-Item -LiteralPath (Join-Path $SourceDir "scripts") -Destination $Target -Recurse -Force
Copy-Item -LiteralPath (Join-Path $SourceDir "references") -Destination $Target -Recurse -Force
Copy-Item -LiteralPath (Join-Path $SourceDir "data") -Destination $Target -Recurse -Force
Copy-Item -LiteralPath $Shared -Destination (Join-Path $Target "shared") -Recurse -Force
Write-Host "Installed $Name → $Target"


param(
    [string]$ClaudeHome = "$env:USERPROFILE\.claude"
)

$ErrorActionPreference = "Stop"
$SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Name = Split-Path -Leaf $SourceDir
$SkillTarget = Join-Path $ClaudeHome "skills\$Name"
$RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $SourceDir "..\.."))
$SharedSource = Join-Path $RepoRoot "shared"
$DataSource = Join-Path $SourceDir "data"
$LegacyCommand = Join-Path $ClaudeHome "commands\$Name.md"

$Python = $null
foreach ($Candidate in @("python3", "python")) {
    try {
        $Version = & $Candidate --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $VersionTuple = & $Candidate -c "import sys; print(sys.version_info[:2])" 2>&1
            $Major, $Minor = $VersionTuple.Trim("()").Split(",").Trim() |
                ForEach-Object { [int]$_ }
            if ($Major -gt 3 -or ($Major -eq 3 -and $Minor -ge 8)) {
                $Python = $Candidate
                break
            }
        }
    } catch {
        continue
    }
}
if (-not $Python) {
    throw "Python 3.8+ not found"
}

$Required = @(
    (Join-Path $SourceDir "SKILL.md"),
    (Join-Path $SourceDir "doctor.sh"),
    (Join-Path $SourceDir "doctor.ps1"),
    (Join-Path $SourceDir "install.sh"),
    (Join-Path $SourceDir "install.ps1"),
    (Join-Path $SourceDir "scripts"),
    $SharedSource
)
if ($Name -eq "tts-lychee") {
    $Required += $DataSource
}
foreach ($Path in $Required) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required source path is missing: $Path"
    }
}

$ReplaceTargets = @(
    (Join-Path $SkillTarget "scripts"),
    (Join-Path $SkillTarget "shared")
)
if ($Name -eq "tts-lychee") {
    $ReplaceTargets += (Join-Path $SkillTarget "data")
}
foreach ($TargetPath in $ReplaceTargets) {
    if (Test-Path -LiteralPath $TargetPath) {
        Remove-Item -LiteralPath $TargetPath -Recurse -Force
    }
}

New-Item -ItemType Directory -Path $SkillTarget -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $SourceDir "SKILL.md") -Destination (Join-Path $SkillTarget "SKILL.md") -Force
Copy-Item -LiteralPath (Join-Path $SourceDir "doctor.sh") -Destination (Join-Path $SkillTarget "doctor.sh") -Force
Copy-Item -LiteralPath (Join-Path $SourceDir "doctor.ps1") -Destination (Join-Path $SkillTarget "doctor.ps1") -Force
Copy-Item -LiteralPath (Join-Path $SourceDir "install.sh") -Destination (Join-Path $SkillTarget "install.sh") -Force
Copy-Item -LiteralPath (Join-Path $SourceDir "install.ps1") -Destination (Join-Path $SkillTarget "install.ps1") -Force
Copy-Item -LiteralPath (Join-Path $SourceDir "scripts") -Destination $SkillTarget -Recurse -Force
Copy-Item -LiteralPath $SharedSource -Destination (Join-Path $SkillTarget "shared") -Recurse -Force
if ($Name -eq "tts-lychee") {
    Copy-Item -LiteralPath $DataSource -Destination (Join-Path $SkillTarget "data") -Recurse -Force
}

if (Test-Path -LiteralPath $LegacyCommand) {
    Remove-Item -LiteralPath $LegacyCommand -Force
    Write-Host "Removed legacy single-file command: $LegacyCommand"
}

Write-Host "Installed $Name → $SkillTarget"
Write-Host "Set LYCHEE_API_KEY before use (or TTS_API_KEY as fallback). Get one from https://shanhaistudio.lycheeai.com.cn/"

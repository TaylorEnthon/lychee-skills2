$ErrorActionPreference = "Stop"

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillsDir = Join-Path $HOME ".claude\skills"
$CommandsDir = Join-Path $HOME ".claude\commands"

Write-Host "== 安装所有 lychee skills =="
New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null
$SkillDirs = Get-ChildItem -LiteralPath (Join-Path $Here "skills") -Directory |
    Where-Object { $_.Name -like "*-lychee" } |
    Sort-Object Name
foreach ($SkillDir in $SkillDirs) {
    $Installer = Join-Path $SkillDir.FullName "install.ps1"
    if (-not (Test-Path -LiteralPath $Installer -PathType Leaf)) {
        continue
    }
    Write-Host "  -> $($SkillDir.Name)"
    try {
        & $Installer
    } catch {
        Write-Host "WARN: $($SkillDir.Name) install 失败：$($_.Exception.Message)"
    }
}

Write-Host "== 安装跨 skill commands =="
New-Item -ItemType Directory -Force -Path $CommandsDir | Out-Null
$CommandFiles = Get-ChildItem -Path (Join-Path $Here "commands\*.md") -File
foreach ($CommandFile in $CommandFiles) {
    Copy-Item -LiteralPath $CommandFile.FullName -Destination $CommandsDir -Force
    Write-Host "  -> $($CommandFile.Name)"
}

$GitHooksDir = Join-Path $Here ".git/hooks"
$SourceHook = Join-Path $Here ".githooks/pre-commit"
if (Test-Path -LiteralPath $SourceHook) {
    if (-not (Test-Path -LiteralPath $GitHooksDir)) {
        New-Item -ItemType Directory -Path $GitHooksDir -Force | Out-Null
    }
    Copy-Item -LiteralPath $SourceHook -Destination (Join-Path $GitHooksDir "pre-commit") -Force
    Write-Host "Installed pre-commit hook"
}

Write-Host "== 完成 =="
Write-Host "已安装：9 个 skill + 2 个跨 skill command"
Write-Host "运行 /lychee-doctor 自检；运行 /lychee-set-key 设置 API key"

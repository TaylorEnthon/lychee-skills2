$ErrorActionPreference = "Stop"

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Name = Split-Path -Leaf $Here
$Target = Join-Path $HOME ".claude\skills\$Name"
$ScriptsTarget = Join-Path $Target "scripts"
$SharedSource = [System.IO.Path]::GetFullPath((Join-Path $Here "..\shared"))
$SharedTarget = Join-Path $Target "shared"
$DataSource = Join-Path $Here "data"
$DataTarget = Join-Path $Target "data"

New-Item -ItemType Directory -Force -Path $ScriptsTarget, $SharedTarget, $DataTarget | Out-Null
Copy-Item -Force (Join-Path $Here "SKILL.md") $Target
Copy-Item -Force (Join-Path $Here "scripts\*.py") $ScriptsTarget
Copy-Item -Force @(
    (Join-Path $Here "doctor.sh"),
    (Join-Path $Here "doctor.ps1"),
    (Join-Path $Here "install.sh"),
    (Join-Path $Here "install.ps1")
) $Target
Copy-Item -Recurse -Force (Join-Path $SharedSource "*") $SharedTarget
Copy-Item -Recurse -Force (Join-Path $DataSource "*") $DataTarget
Write-Host "$Name 安装到 $Target"

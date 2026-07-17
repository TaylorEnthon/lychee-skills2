$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = $null
foreach ($Candidate in @("python3", "python")) {
    try {
        & $Candidate --version 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { $Python = $Candidate; break }
    } catch { continue }
}
if (-not $Python) { throw "未找到 Python 3" }
& $Python -c "import requests; print('requests', requests.__version__)"
if (-not $env:LYCHEE_API_KEY) {
    Write-Host "WARN: LYCHEE_API_KEY 未设置。运行 /lychee-set-key 配置。"
} else {
    Write-Host "OK: API key 已设置"
}
& $Python -m py_compile (Join-Path $Here "scripts\synthesize.py") (Join-Path $Here "scripts\list_voices.py") (Join-Path $Here "scripts\list_tasks.py")
$Cache = Join-Path $Here "data\voices-cache.json"
if (-not (Test-Path -LiteralPath $Cache)) {
    Write-Host "WARN: 音色缓存不存在；需要时运行 list_voices.py"
} else {
    $Updated = [DateTimeOffset]::Parse((Get-Content -Raw -LiteralPath $Cache | ConvertFrom-Json).updated_at)
    if ([DateTimeOffset]::UtcNow - $Updated -ge [TimeSpan]::FromHours(24)) { Write-Host "WARN: 音色缓存已过期；运行 list_voices.py --refresh" } else { Write-Host "OK: 音色缓存有效" }
}
Write-Host "== doctor OK =="

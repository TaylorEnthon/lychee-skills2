$ErrorActionPreference = "Stop"

$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Shared = Join-Path $Here "shared"
if (-not (Test-Path -LiteralPath $Shared -PathType Container)) {
    $RepositoryShared = [System.IO.Path]::GetFullPath((Join-Path $Here "..\shared"))
    if (Test-Path -LiteralPath $RepositoryShared -PathType Container) {
        $Shared = $RepositoryShared
    }
}

Write-Host "== 检查 Python =="
$Python = $null
foreach ($Candidate in @("python3", "python")) {
    try {
        $Version = & $Candidate --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $Python = $Candidate
            break
        }
    } catch {
        continue
    }
}
if (-not $Python) {
    throw "未找到可用的 Python 3"
}
Write-Host $Version

Write-Host "== 检查 requests 依赖 =="
& $Python -c "import requests; print('requests', requests.__version__)"

Write-Host "== 检查 API key =="
$ApiKey = $env:LYCHEE_API_KEY
if ([string]::IsNullOrEmpty($ApiKey)) {
    Write-Host "WARN: LYCHEE_API_KEY 未设置。运行 /lychee-set-key 配置。"
} else {
    $PrefixLength = [Math]::Min(8, $ApiKey.Length)
    Write-Host "OK: API key 已设置（前 8 位）=$($ApiKey.Substring(0, $PrefixLength))..."
}

Write-Host "== 检查 shared/ 能 import =="
if (-not (Test-Path -LiteralPath $Shared -PathType Container)) {
    Write-Host "WARN: shared/ 未安装，请重新运行当前 skill 的 install"
} else {
    $PythonCode = @"
import sys
sys.path.insert(0, r'''$Shared''')
from auth import get_api_key, API_KEY_HEADER
from http_client import BASE_URL, post_multipart, get_json, poll_status
from ws_client import TTS_WS_URL
print('shared/ OK')
print('BASE_URL =', BASE_URL)
print('TTS_WS_URL =', TTS_WS_URL)
print('API_KEY_HEADER =', API_KEY_HEADER)
"@
    & $Python -c $PythonCode
}

Write-Host "== 检查 HTTP base 可达 =="
$Health = Invoke-RestMethod -Uri "https://shanhaistudio.lycheeai.com.cn/openapi/open/health" -Method Get
$Health | ConvertTo-Json -Compress
Write-Host "== doctor OK =="

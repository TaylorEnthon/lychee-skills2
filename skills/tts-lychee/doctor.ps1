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

Write-Host "== 检查 websocket-client 依赖 =="
& $Python -c "import websocket; print('websocket-client', websocket.__version__)"

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
    $SharedCode = @"
import sys
sys.path.insert(0, sys.argv[1])
from ws_client import TTS_WS_URL, tts_synthesize
expected = 'wss://shanhaistudio.lycheeai.com.cn/openapi/tts/ws_binary/v2'
if TTS_WS_URL != expected:
    raise SystemExit('TTS_WS_URL mismatch: ' + TTS_WS_URL)
print('shared/ OK')
print('TTS_WS_URL =', TTS_WS_URL)
"@
    & $Python -c $SharedCode $Shared
}

Write-Host "== 检查 data/ 与音色规则 =="
$VoiceCode = @"
import sys
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, sys.argv[2])
from synthesize import REQUIRED_VOICES, load_voice_data, resolve_voice_id
alias_map, presets, voice_aliases = load_voice_data()
print('data JSON OK:', len(presets), 'presets,', len(alias_map), 'aliases,', len(voice_aliases), 'voice groups')
print('required voices OK:', ', '.join(REQUIRED_VOICES))
print('required aliases OK:', ', '.join(REQUIRED_VOICES))
voice_id, used_default, matched = resolve_voice_id('性感的女声', alias_map, presets, voice_aliases)
if voice_id != '性感女声' or used_default:
    raise SystemExit('音色匹配失败: ' + voice_id)
print('voice matching OK: 性感的女声 ->', voice_id, '(matched:', matched + ')')
"@
& $Python -c $VoiceCode $Shared (Join-Path $Here "scripts")

Write-Host "== doctor OK =="

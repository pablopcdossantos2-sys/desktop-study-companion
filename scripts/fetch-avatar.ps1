$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$avatarDir = Join-Path $projectRoot "assets\avatar"
$target = Join-Path $avatarDir "Sendagaya_Shino.vrm"

# CC0 model selected for Desktop Study Companion.
# Official page:
# https://hub.vroid.com/en/characters/4593660874193246717/models/7956589129305596116
# Public mirror containing the same CC0 VRM 1.0 file:
$url = "https://raw.githubusercontent.com/yw0nam/YUI/main/resources/vrms/Sendagaya_Shino.vrm"
$expectedSha256 = "fab70124f0025e444a6eef84d6ab3a04e78c0adb626099e54b55287d0f083a47"

New-Item -ItemType Directory -Force -Path $avatarDir | Out-Null

if (Test-Path $target) {
    $existing = (Get-FileHash -Algorithm SHA256 $target).Hash.ToLowerInvariant()
    if ($existing -eq $expectedSha256) {
        Write-Host "Avatar VRM já está presente e validado." -ForegroundColor Green
        exit 0
    }
    Write-Host "Avatar existente não corresponde ao SHA-256 esperado; baixando novamente." -ForegroundColor Yellow
}

Write-Host "Baixando Sendagaya_Shino.vrm (CC0)..."
Invoke-WebRequest -Uri $url -OutFile $target

$actual = (Get-FileHash -Algorithm SHA256 $target).Hash.ToLowerInvariant()
if ($actual -ne $expectedSha256) {
    Remove-Item $target -Force -ErrorAction SilentlyContinue
    throw "Falha de integridade do avatar. SHA-256 recebido: $actual"
}

Write-Host "Avatar baixado e validado." -ForegroundColor Green

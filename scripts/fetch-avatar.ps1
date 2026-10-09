$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$avatarDir = Join-Path $projectRoot "assets\avatar"
$target = Join-Path $avatarDir "Sendagaya_Shino.vrm"

# CC0 model selected for Desktop Study Companion.
# Official page:
# https://hub.vroid.com/en/characters/4593660874193246717/models/7956589129305596116
$urls = @(
    "https://github.com/pablopcdossantos2-sys/desktop-study-companion/releases/download/avatar-assets-v1/Sendagaya_Shino.vrm",
    "https://raw.githubusercontent.com/yw0nam/YUI/main/resources/vrms/Sendagaya_Shino.vrm"
)
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
$success = $false
foreach ($url in $urls) {
    try {
        Write-Host "Tentando: $url"
        Invoke-WebRequest -Uri $url -OutFile $target
        $actual = (Get-FileHash -Algorithm SHA256 $target).Hash.ToLowerInvariant()
        if ($actual -eq $expectedSha256) {
            $success = $true
            break
        }
        Write-Host "SHA-256 inesperado: $actual" -ForegroundColor Yellow
    } catch {
        Write-Host "Fonte indisponível: $url" -ForegroundColor Yellow
    }
    Remove-Item $target -Force -ErrorAction SilentlyContinue
}

if (-not $success) {
    Remove-Item $target -Force -ErrorAction SilentlyContinue
    throw "Não foi possível obter uma cópia válida do avatar."
}

Write-Host "Avatar baixado e validado." -ForegroundColor Green

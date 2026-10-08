$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host ""
Write-Host "Desktop Study Companion - ambiente de desenvolvimento" -ForegroundColor Cyan
Write-Host "Pasta do projeto: $projectRoot"
Write-Host ""

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        try {
            & py -3.12 --version *> $null
            if ($LASTEXITCODE -eq 0) {
                return @("py", "-3.12")
            }
        } catch {}
        try {
            & py -3.11 --version *> $null
            if ($LASTEXITCODE -eq 0) {
                return @("py", "-3.11")
            }
        } catch {}
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }

    throw "Python não foi encontrado. Consulte docs/TUTORIAL-INSTALACAO-WINDOWS.md."
}

$python = Get-PythonCommand
Write-Host "Python encontrado: $($python -join ' ')" -ForegroundColor Green

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Criando ambiente virtual .venv..."
    if ($python.Count -eq 2) {
        & $python[0] $python[1] -m venv .venv
    } else {
        & $python[0] -m venv .venv
    }
}

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

Write-Host "Atualizando pip..."
& $venvPython -m pip install --upgrade pip

Write-Host "Instalando/atualizando o projeto e dependências..."
& $venvPython -m pip install -e ".[dev]"

Write-Host "Executando testes rápidos..."
& $venvPython -m pytest
if ($LASTEXITCODE -ne 0) {
    throw "Os testes falharam. Não iniciarei a aplicação para evitar mascarar o erro."
}

Write-Host ""
Write-Host "Iniciando o Desktop Study Companion..." -ForegroundColor Cyan
Write-Host "Dica: clique com o botão direito no personagem para iniciar uma sessão."
Write-Host ""

& $venvPython -m desktop_study_companion.app

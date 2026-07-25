<#
.SYNOPSIS
    Builda o MailCerto em um executável .exe portátil (one-file) para Windows
    usando PyInstaller.

.DESCRIPTION
    - Regenera os ícones (PNG/ICO) a partir do SVG usando scripts/generate_icons.py
    - Roda o PyInstaller com o MailCerto.spec (inclui ícone, metadados, recursos)
    - Valida que o executável foi criado

.EXAMPLE
    .\scripts\build_windows.ps1
#>

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> [1/4] Verificando Python e PyInstaller..." -ForegroundColor Cyan
python -c "import sys; print(f'Python {sys.version}')"
if ($LASTEXITCODE -ne 0) { throw "Python não encontrado no PATH." }

python -m pip show pyinstaller > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Instalando PyInstaller..." -ForegroundColor DarkYellow
    python -m pip install --quiet "pyinstaller>=6.5.0" "pyinstaller-hooks-contrib>=2023.0"
    if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar PyInstaller." }
}

Write-Host "==> [2/4] Gerando recursos de ícone (PNG/ICO)..." -ForegroundColor Cyan
python scripts\generate_icons.py
if ($LASTEXITCODE -ne 0) { throw "Falha ao gerar os ícones." }

Write-Host "==> [3/4] Rodando PyInstaller (one-file GUI)..." -ForegroundColor Cyan
python -m PyInstaller --clean --noconfirm MailCerto.spec
if ($LASTEXITCODE -ne 0) { throw "Falha no build PyInstaller." }

$ExePath = Join-Path $Root "dist\MailCerto.exe"
Write-Host "==> [4/4] Validando saída..." -ForegroundColor Cyan
if (-not (Test-Path $ExePath)) {
    throw "Executável não encontrado em: $ExePath"
}
$SizeMB = [math]::Round((Get-Item $ExePath).Length / 1MB, 1)
Write-Host ""
Write-Host "==== BUILD CONCLUÍDO ====" -ForegroundColor Green
Write-Host "  Executável: $ExePath"
Write-Host "  Tamanho...: $SizeMB MB"
Write-Host "  Arquivos auxiliares (build/) podem ser apagados se não for rebuildar."
Write-Host "  Copie apenas dist\MailCerto.exe para a máquina alvo."

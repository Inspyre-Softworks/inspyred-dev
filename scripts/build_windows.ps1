$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'Failed to upgrade pip.' }

python -m pip install -e '.[dev]'
if ($LASTEXITCODE -ne 0) { throw 'Failed to install build dependencies.' }

python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Tests failed; Windows bundle was not built.' }

python -m PyInstaller --clean --noconfirm packaging/InspyredDev.spec
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed to create the Windows bundle.' }

Write-Host ''
Write-Host 'Windows bundle created at:' -ForegroundColor Green
Write-Host '  dist/InspyredDev/InspyredDev.exe'

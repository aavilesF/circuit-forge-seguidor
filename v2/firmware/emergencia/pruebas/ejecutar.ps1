# Robot de emergencia · pruebas en la PC desde PowerShell (Windows). Requiere g++ (MinGW/WinLibs) y Python en el PATH.
# Uso:  .\ejecutar.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force ..\.build | Out-Null
$S = "..\emergencia"
& g++ -std=c++17 -Wall -Wextra -Werror -O1 "-I$S" test_emergencia.cpp `
  "$S\posicion.cpp" "$S\pid.cpp" "$S\control.cpp" "$S\filtro.cpp" "$S\motor.cpp" "$S\estados.cpp" `
  "$S\indicadores.cpp" "$S\ajustes.cpp" -o ..\.build\test_emergencia.exe
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& ..\.build\test_emergencia.exe
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& python verificar_pines.py
exit $LASTEXITCODE

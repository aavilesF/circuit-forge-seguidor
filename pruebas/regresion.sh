#!/usr/bin/env bash
# Regresión completa en la laptop (sin ESP32). Uso: pruebas/regresion.sh
# 1) pruebas unitarias  2) mismas pruebas con AddressSanitizer/UBSan  3) cppcheck (si está instalado)
# 4) sintaxis del firmware contra stub de Arduino  5) escenarios del simulador con criterios de aceptación
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build
F="firmware/seguidor/posicion.cpp firmware/seguidor/pid.cpp firmware/seguidor/control.cpp firmware/seguidor/estados.cpp"
echo "== 1. pruebas unitarias"; pruebas/ejecutar.sh
echo "== 2. sanitizers"
g++ -std=c++17 -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=all -Wall -Wextra pruebas/test_logica.cpp $F -o .build/test_asan
.build/test_asan
echo "== 3. análisis estático"
if command -v cppcheck >/dev/null; then
  if cppcheck --enable=warning,performance,portability --std=c++17 --error-exitcode=1 -q $F sim/simular.cpp; then echo "cppcheck: sin advertencias"
  else echo "cppcheck: HAY ADVERTENCIAS"; exit 1; fi
else echo "cppcheck no instalado (opcional: pip install cppcheck)"; fi
echo "== 4. sintaxis del firmware (stub, NO es compilación real para ESP32)"; pruebas/verificar_sintaxis_esp32.sh
echo "== 5. escenarios del simulador (controlador PD por defecto, vbase 0.6)"
python3 - <<'PY'
import csv, subprocess, sys
fallas = 0
for etiqueta, extra in (("QTR-8A", []), ("curvo 24", ["sensores=24", "geom=arco", "paso=4", "radio_arco=80"])):
    out = subprocess.run(["sim/ejecutar.sh", "vbase=0.6", "modo=escenarios", *extra], capture_output=True, text=True, check=True).stdout
    for r in csv.DictReader(l for l in out.splitlines() if not l.startswith("#")):
        ok = r["ok"] == "1"
        if r["escenario"] != "fin_de_linea":
            ok = ok and float(r["err_max_mm"]) <= 35 and int(r["perdidas"]) == 0
        else:
            ok = ok and float(r["t_parada_s"]) < 1.0
        if not ok: fallas += 1
        print(f"  {'OK ' if ok else 'FALLA'} {etiqueta:9} {r['escenario']:17} err_max={r['err_max_mm']:>5} mm  perdidas={r['perdidas']}  t_parada={r['t_parada_s']}")
sys.exit(1 if fallas else 0)
PY
echo "REGRESIÓN COMPLETA: OK"

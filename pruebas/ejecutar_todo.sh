#!/usr/bin/env bash
# Todas las pruebas reproducibles del proyecto (sin hardware). Uso: pruebas/ejecutar_todo.sh
# Requisitos: python3 con numpy, numba, PyYAML, matplotlib; g++ (C++17).
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== 1. Configuración maestra sincronizada con el firmware"
python3 herramientas/generar_config_firmware.py --verificar
echo "== 2. Física del simulador contra soluciones analíticas"
python3 sim/pruebas/test_fisica.py
echo "== 3. Controlador del simulador = controlador del firmware (vectores dorados)"
(cd pruebas/sf && python3 generar_dorados.py > /dev/null)
python3 sim/pruebas/test_control.py
echo "== 4. Lógica del firmware en C++ (ASan/UBSan) contra Python y contra el simulador"
pruebas/sf/ejecutar.sh
echo "== 5. Sintaxis del firmware completo contra el stub de Arduino (NO es compilar para el MCU)"
pruebas/sf/verificar_sintaxis_sf.sh
echo "== 6. Pistas sintéticas dentro del reglamento"
python3 -c "
import sys; sys.path.insert(0, 'sim')
import importlib.util, math
spec = importlib.util.spec_from_file_location('f1', 'sim/fase1/calculos_fisicos.py'); m = importlib.util.module_from_spec(spec)
sys.modules['f1'] = m; spec.loader.exec_module(m)
ok = all(m.validar_pista(p)['cumple'] for p in m.pistas())
print('4/4 pistas cumplen el reglamento' if ok else 'PISTA FUERA DE REGLAMENTO'); sys.exit(0 if ok else 1)"
echo "== 7. Verificación eléctrica (pines, dominios de voltaje, límites del driver)"
python3 hardware/electronics/verificar_electrica.py
echo "== 8. Disposición mecánica (caja del reglamento, choques, CG)"
python3 hardware/mechanical/disposicion.py | tail -3
echo "== 9. Presupuesto (BOM contra el límite del YAML)"
python3 herramientas/presupuesto.py
echo "TODO OK"

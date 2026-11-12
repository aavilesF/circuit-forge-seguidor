#!/usr/bin/env bash
# Todas las pruebas reproducibles del proyecto (sin hardware). Uso: pruebas/ejecutar_todo.sh
# Requisitos: python3 con numpy, numba, PyYAML, matplotlib, shapely; g++ (C++17);
#             arm-none-eabi-gcc 13+ con newlib (paso 5; si falta, el paso se marca OMITIDO y el script termina en
#             código 2 para que nadie lo confunda con "todo verificado").
# Las verificaciones de KiCad (ERC, DRC, paridad) y del CAD se regeneran con hardware/electronics/generar_fabricacion.sh
# y hardware/mechanical/cad/generar_cad.py; aquí se comprueban sus resultados guardados.
set -euo pipefail
cd "$(dirname "$0")/.."
OMITIDO=0
echo "== 1. Configuración maestra y pines sincronizados con el firmware (YAML + diseño eléctrico -> encabezados)"
python3 herramientas/generar_config_firmware.py --verificar
echo "== 2. Física del simulador contra soluciones analíticas"
python3 sim/pruebas/test_fisica.py
echo "== 3. Controlador del simulador = controlador del firmware (vectores dorados)"
(cd pruebas/sf && python3 generar_dorados.py > /dev/null)
python3 sim/pruebas/test_control.py
echo "== 4. Lógica del firmware en C++ (ASan/UBSan) contra Python y contra el simulador"
pruebas/sf/ejecutar.sh
echo "== 5. Compilación real del firmware para el STM32G431 (arm-none-eabi-gcc, -Werror)"
if command -v arm-none-eabi-gcc >/dev/null 2>&1; then
  (cd firmware/stm32 && make clean >/dev/null && make 2>&1 | tail -4)
  simbolos=$(arm-none-eabi-nm firmware/stm32/build/speed_follower.elf)
  grep -q " T TIM6_DAC_IRQHandler$" <<< "$simbolos"
  grep -q " T USART1_IRQHandler$" <<< "$simbolos"
  echo "vectores TIM6 y USART1 resueltos a las rutinas del firmware"
else
  echo "OMITIDO: no está arm-none-eabi-gcc (ver firmware/README.md)"; OMITIDO=1
fi
echo "== 6. Pistas sintéticas dentro del reglamento"
python3 -c "
import sys; sys.path.insert(0, 'sim')
import importlib.util
spec = importlib.util.spec_from_file_location('f1', 'sim/fase1/calculos_fisicos.py'); m = importlib.util.module_from_spec(spec)
sys.modules['f1'] = m; spec.loader.exec_module(m)
ok = all(m.validar_pista(p)['cumple'] for p in m.pistas())
print('4/4 pistas cumplen el reglamento' if ok else 'PISTA FUERA DE REGLAMENTO'); sys.exit(0 if ok else 1)"
echo "== 7. Diseño eléctrico: reglas propias y conectividad diseño = esquemático = PCB"
python3 hardware/electronics/generador/diseno.py
python3 hardware/electronics/herramientas/verificar_conectividad.py --pcb
echo "== 8. ERC/DRC guardados de KiCad 9 sin errores sin justificar"
python3 hardware/electronics/herramientas/resumen_verificacion.py > /dev/null && echo "RESUMEN.md: sin errores"
echo "== 9. Huellas oficiales y modelos 3D presentes; STEP exportado sin modelos faltantes"
python3 hardware/electronics/herramientas/verificar_modelos3d.py
echo "== 10. Mecánica: caja del reglamento, interferencias, CG y masa del CAD contra el YAML"
python3 hardware/mechanical/verificar_mecanica.py
echo "== 11. BOM final consistente con el diseño (referencias, cantidades, números de parte)"
python3 herramientas/generar_bom.py --verificar
if [[ $OMITIDO == 1 ]]; then echo "PRUEBAS OK, CON PASOS OMITIDOS"; exit 2; fi
echo "TODO OK"

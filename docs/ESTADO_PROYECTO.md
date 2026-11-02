# Estado del proyecto — Speed Follower

Actualizado: 2 nov 2026 · Rama `engineering/speed-follower` (sin fusionar a `main`) · Competencia: 21 nov 2026.
**Ingeniería cerrada para fabricación. Nada está comprado, fabricado, armado ni medido**: todas las validaciones son de
simulación, EDA (KiCad) o CAD.

## Fases

| Fase | Entregables | Estado |
|---|---|---|
| 1. Reglamento y cálculos | `REGLAMENTO_MATRIZ.md`, `CALCULOS_FISICOS.md`, `VERIFICACION_FASE1.md` | Hecha |
| 2. Simulación dinámica | `sim/`, `SIMULACION_DINAMICA.md` §1-4 | Hecha |
| 3. Presupuesto de $2,000 | Commit `033b641` (histórico) | Reemplazada por la fase final |
| **Final. Cierre de ingeniería** | Arquitectura definitiva, BOM de compra, KiCad (esquemático + PCB ruteada), paquete de fabricación, PCBA 2D/3D, CAD mecánico, firmware compilado, manual, validación | **Hecha (CAD/EDA/simulación)** |
| Construcción y medición | Fabricar, ensamblar, pruebas E1-E9, mediciones M1-M8, pista de práctica | **Pendiente** (requiere las piezas) |

## Lista de entrega

| Entregable | Estado | Dónde |
|---|---|---|
| BOM con números de parte exactos y cantidades | **Hecho** (46 partidas, categorías A-G; cada número de parte con su fuente de verificación) | `docs/BOM_FINAL.csv`, `hardware/electronics/fabricacion/bom_ensamblaje.csv` |
| Motores y transmisión definitivos | **Hecho**: Pololu #3048 (HPCB 12 V 10:1, eje extendido) + encoders #4760 + llantas #1087 | `docs/ARQUITECTURA.md` §1-2 |
| Esquemático KiCad completo | **Hecho**: 5 hojas, 131 partes, 78 redes; ERC con 2 avisos justificados | `hardware/electronics/kicad/`, `fabricacion/esquematico.pdf` |
| PCB ruteada, DRC y ERC | **Hecho**: 4 capas, 680 pistas, 198 vías, planos GND/+3V3; DRC 0 violaciones, 0 sin conectar, 0 problemas de paridad | `hardware/electronics/verificacion/RESUMEN.md` |
| PCBA 2D con referencias y dimensiones | **Hecho** | `hardware/electronics/pcba/pcba_2d_*.svg`, `fabricacion/ensamblaje_*.pdf` |
| PCBA 3D con componentes posicionados | **Hecho**: 109 componentes con modelo oficial de KiCad 9 (2 aproximados marcados: XT30 y PTC) | `hardware/electronics/pcba/pcba_3d_*.png`, `verificacion/modelos3d.md` |
| STEP de la PCBA y del robot completo | **Hecho**: STEP de la PCBA comparado componente por componente contra la PCB; ensamble del robot | `fabricacion/speed_follower_pcba.step`, `hardware/mechanical/step/robot_completo.step` |
| Gerbers, taladros y pick and place | **Hecho** (solo se generan si ERC/DRC/paridad/conectividad pasan) | `hardware/electronics/fabricacion/` |
| Firmware con compilación real | **Hecho**: compila con arm-none-eabi-gcc 13.2.1 sin avisos (`-Werror`), 16.2 KB de flash. **No probado en un STM32 físico** | `firmware/`, `firmware/stm32/registro_compilacion.txt` |
| Manual de montaje y calibración | **Hecho** | `docs/MANUAL_ENSAMBLAJE.md` |

## Pendientes, en orden

| # | Pendiente | Bloquea |
|---|---|---|
| 1 | Confirmar la inscripción y enviar las preguntas de `REGLAMENTO_MATRIZ.md` §5 | Participar |
| 2 | Comprar según `BOM_FINAL.csv`; pedir la PCB (con o sin ensamblaje) y las 6 piezas de PA12 | Todo |
| 3 | Ensamblar y correr las pruebas E1-E9 del manual (sin batería → fuente limitada → programación → sensores → motores → pista) | Validación física |
| 4 | Mediciones M1 (μ), M2/M5 (masa y reparto: **CG**), M7 (motor), M8 (sensores) → YAML → `python3 sim/fase_final.py F` | Velocidad de competencia |
| 5 | Pista de práctica (fórmica + vinil de 2.5 cm) | Ajuste fino |

## Limitaciones vigentes

- **Validación física: ninguna.** ERC/DRC prueban que la PCB coincide con el esquemático y cumple sus reglas; el CAD prueba
  que las piezas caben; la simulación prueba el control sobre un modelo. Nada de eso sustituye a las pruebas E1-E9.
- Datos supuestos que se miden al armar: inercia del rotor, μ, señal de los sensores a 3.05 mm, reparto de peso real.
- Sensibilidad principal: el **CG adelantado** (10 mm más adelante → 80 % de éxito simulado). Ver `AUDITORIA_ROBUSTEZ.md`.
- Modelos 3D aproximados: conector XT30 y fusible PTC (contorno de la huella oficial), y en el CAD mecánico motor, llanta,
  batería y bola (medidas de ficha).
- Pistas sintéticas; el circuito real se conoce el día del evento.

## Evidencia reproducible

| Comando | Salida |
|---|---|
| `pruebas/ejecutar_todo.sh` | 11 grupos de pruebas; última corrida en `pruebas/registro_ejecutar_todo.txt` (TODO OK) |
| `hardware/electronics/generar_fabricacion.sh` | KiCad 9: esquemático, PCB, ERC, DRC con paridad, paquete de fabricación, vistas |
| `python3 hardware/mechanical/cad/generar_cad.py` · `python3 hardware/mechanical/verificar_mecanica.py` | CAD, STEP/STL, planos, vistas; verificación mecánica |
| `python3 sim/fase_final.py Z R E S F G` | Selección de motor, sensibilidad, control, validación (`sim/resultados/final/`) |
| `cd firmware/stm32 && make` | Firmware (`build/speed_follower.hex`) |
| `python3 hardware/electronics/herramientas/calculos_electricos.py` | `docs/CALCULOS_ELECTRICOS.md` |

Versiones usadas: Python 3.13.17, numpy 2.5.3, numba 0.68.1, scipy 1.18.1, shapely 2.2.0, PyYAML 6.0.3, matplotlib 3.11.2,
CadQuery 2.8.0, KiCad 9.0.8, g++ 13.3.0, arm-none-eabi-gcc 13.2.1.

> **HISTÓRICO (rama anterior `engineering/robot-casero`). No es información vigente de V2.** Inventario, decisiones y pendientes vigentes: `v2/inventario.csv`, `v2/docs/decisiones.md`, `docs/pendientes-por-confirmar.md`. Estado de cada documento: `v2/docs/ESTADO-DOCUMENTOS.md`.

# Contexto para un chat nuevo: Seguidor de Línea V2 (robot casero)

Actualizado: 11 nov 2026 (noche). Rama: `engineering/robot-casero`. HEAD local: `668607a`. **Sin push** (Alan no autorizó el push al remoto).

## 1. Quién es Alan y cómo quiere trabajar
- Estudiante hispanohablante, equipo de 3 para la competencia Robolympics (reglamento: 20×10 cm, 500 g, sin inalámbrico, sin kits). Competencia el 21 nov 2026; cambios al reglamento el 18 nov.
- Responder SIEMPRE en español. Tablas para pendientes y rutas de archivos.
- Acciones: **no hacer push sin autorización explícita**; no trabajar en `main`; commits locales sí se pueden hacer. No inventar medidas (marcarlas en `docs/pendientes-por-confirmar.md`). No volver a pedir datos que ya dio. No afirmar uso del MCP si no se usó.
- Archivos que devuelve al usuario: mismo nombre que el original, sin sufijos.
- Prefiere "empieza ejecutando, no solo plan", pero quiere informes claros con secciones.
- Alan NO está convencido del estado actual de las PCB: "hay que pulir muchos detalles". Quiere un chat nuevo con la idea y el contexto, no con el ruteo como cierre.

## 2. El proyecto
- Robot seguidor de línea casero. Chasis de acrílico (opción A: una sola base), dos motores N20 con llantas ∅26.7×21.7 mm, rueda loca "Mini rueda universal 3Pi N20" 22×16×15 mm (medidas UNIT verdaderas, no volver a pedirlas), asegurador N20 solo mecánico, ventilador 4010 12 V.
- Electrónica: ESP32 DevKit 30 pines (USB-C), driver DRV8833 (módulo comprado), 2× MP1584 (uno a 5.0 V para el ESP32 por VIN vía D2 1N5822; otro a 6.0 V para motores), batería LiPo 2S 7.4 V 450–500 mAh (aún por comprar, tope de $1,800 MXN), interruptor KCD1 cableado (no en PCB), fusible PTC reseteable provisional (sin corriente nominal inventada, P16/M28), MOSFET IRLZ44N para el ventilador, 1N5822 a ~20 mm.
- Sensores: 12 TCRT5000 (+2 de repuesto) montados abajo en la placa de sensores, multiplexor 74HC4067, transistor 2N2222 H331 (E-B-C viendo la cara plana) como interruptor de emisores, resistencias 330 Ω (LED) y 10 kΩ. Cable de 8 hilos a la principal (J5: +3V3, GND, S0–S3, SIG, EMIT_EN). Sin zumbador (P14).
- Botones: START (GPIO4), CAL (GPIO14), RESET (EN). Batería: divisor 100k/33k a GPIO36 (VP).
- Pines ESP32 (fuente: `electronica/kicad/pines_robot_casero.h`): mux S0=25, S1=26, S2=27, S3=33, SIG=34 (ADC1), emisores=13; motores AIN1=19, AIN2=21, BIN1=22, BIN2=23, SLEEP=16; ventilador=17.
- Firmware por alinear (P18): `config.h` con START=4, sin zumbador, ventilador=17, `SENSORES_DIRECTOS 0`.
- Mecánica: `mecanica/autocad/parametros.yaml` (llanta 26.7/21.7, motor 24.5/12/10, eje 8.5, asegurador 19.5, rueda_loca). `generar_dxf.py` corregido (quitado +3.81) pero **DXF sin regenerar** (C10).

## 3. Repositorio y archivos clave
- Repo: https://github.com/aavilesF/circuit-forge-seguidor. Clon en `/home/claude/circuit-forge-seguidor`. Remoto `origin` apunta ahí; `main` tracking `origin/main`.
- `docs/pendientes-por-confirmar.md` (V7, fuente de verdad de IDs: M, P, C, E, R, V, D). Historial en `docs/historial/` (v6 es el anterior).
- `docs/especificaciones-componentes.md`, `docs/decisiones-robot-casero.md` (D18–D24: D18 = PCB doble cara), `robot-casero/materiales/BOM.csv`, `robot-casero/materiales/CHECKLIST.md`, `docs/faltantes-unit.md`. `docs/robot-casero/*` = plan B HISTÓRICO.
- `docs/contexto-ramas.md`, `docs/opciones-diseno.md` (O04 descartada: pegar dos placas).
- `electronica/kicad/`: `principal/`, `sensores/`, `robot_casero.pretty/` (huellas propias), `herramientas/`, `NOTAS.md`, `FABRICACION_CASERA.md`, `pines_robot_casero.h`.
- Generadores (`electronica/kicad/herramientas/`): `generar_principal.py`, `generar_sensores.py` (esquemáticos), `huellas_propias.py`, `generar_pcb.py` (colocación + ruteo + DRC; `--sin-ruteo`), `ruteador.py` (enrutador propio), `verificar_esquematico.py`, `exportar_fabricacion.py`.
- Entorno: KiCad 7.0.11 en el contenedor (`python3.12` con `pcbnew`, `kicad-cli`; `export KICAD7_FOOTPRINT_DIR=/usr/share/kicad/footprints`). No usar `python3.12 -I` con pcbnew.
- Freerouting: bloqueado por el clasificador en este entorno. No buscar rodeos; Alan puede correrlo desde KiCad 10.

## 4. Decisiones de diseño tomadas (no reabrir sin motivo)
- **PCB doble cara casera** (D18): una sola fenólica con cobre en ambas caras (no dos placas pegadas). Sin metalizado: vías = agujero 0.8 mm + alambre soldado por las dos caras. Pista 0.8 mm, separación 0.5 mm, pads 1.8 mm, vía 1.8/0.8 mm. Brocas: 0.8 (resistencias, sensores, vías), 1.0 (headers, módulos, TO-220, PTC), 1.3 (1N5822), 3.2 (M3).
- TCRT5000 montados abajo (volteados), se sueldan por arriba. Resistencias y D/Q en ambas caras. Módulos, headers, botones y capacitores solo abajo. Las patas PTH cuentan como cobre en ambas caras (KiCad 10).
- Esquemático: multiplexor + 12 TCRT5000 + 2N2222 en la placa de sensores; cable de 8 hilos a la principal.

## 5. Estado actual (honesto)
| Placa | Tamaño | Ruteo | Vías | DRC KiCad 7 | DRC/ERC KiCad 10 (MCP) | Estado |
|---|---|---|---|---|---|---|
| sensores | 94×75 mm | 0 conexiones faltantes | 37 | 0 errores (12 avisos) | 0 / 0 errores (226 `endpoint_off_grid`) | C (verificada) |
| principal | 90×106 mm | 0 faltantes | 30 | 0 errores (30 avisos serigrafía) | 0 / 0 errores (15 `endpoint_off_grid`, 3 `pin_to_pin`) | C (verificada) |

- Estados: A = diseño, B = ruteada, C = verificada (ERC/DRC limpios), D = lista para fabricar (requiere huellas confirmadas).
- Fabricación exportada: `principal/fabricacion/` y `sensores/fabricacion/` (patrones 1:1 cara abajo, cara arriba en espejo, perforaciones CSV/PDF, `*_soldar_arriba.csv`, LEEME).
- Verificación KiCad 10: JSON en `<placa>/verificacion_kicad10/`.
- **Problemas que Alan intuye y que hay que pulir** (no son todos verificados):
  - Placa de sensores: 94×75 mm. Con la rueda y la placa, el robot pasa de 200 mm de largo (C10 / R01). Opción B propuesta: ventilador fuera de la principal. Decisión pendiente.
  - Principal: colocación apretada; el ESP32 quedó a la derecha con el DRV8833 girado 180°. Hay muchas vías (30) y trazas largas; el ruteo es del enrutador propio, no optimizado.
  - Huellas provisionales: TCRT5000 (M19, M20), módulo 74HC4067 (M17), MP1584 agujeros (M33), PTC (sin corriente, P16). Sin eso no hay estado D.
  - Rueda loca de 15 mm no cabe bajo la base (~3.9 mm del piso) (R03).
  - Fusible PTC provisional.
  - Rin 2.3 mm vs eje 3 mm (P19).
  - Serigrafía: avisos de clip con la máscara y el borde (cosmético).
  - Dianas de alineación en M3; regla de 50 mm para escala al imprimir (no "ajustar a página").
  - DXF de chasis sin regenerar.
  - Ninguna prueba eléctrica real.
- Errores ya corregidos (no repetir): TCRT5000 tratados como arriba (ahora abajo); pads completos en ambas caras (KiCad 10 los marcó si se recortaban); `track_dangling` por tramos pad-celda en ambas caras (corregido); redes "fijas" tapaban salidas (eliminadas); `fp.Flip` antes de `b.Add` → segfault.

## 6. Pendientes para pasar a D (lo que hay que pedirle a Alan)
| ID | Qué falta |
|---|---|
| M19 | TCRT5000: distancia entre filas de patas y paso entre patas |
| M20 | Qué pata del TCRT5000 es ánodo/cátodo del LED y colector/emisor |
| M17 | Foto o lista de pines del 74HC4067 y separación entre sus filas |
| M33 | Agujeros del MP1584 |
| R03 | Altura de la esfera bajo las orejas de la rueda loca |
| R01 | Decisión: ventilador fuera de la principal (opción B) o reacomodo |
| P19 | Rin 2.3 mm vs eje 3 mm |
| P13, P18 | Alinear `config.h` del firmware |
| E01, E02 | Ajustar MP1584 a 5.0 V y 6.0 V con multímetro antes de conectar |

## 7. Proceso de trabajo sugerido para el chat nuevo
1. Leer `docs/pendientes-por-confirmar.md` (V7) y este archivo.
2. Decidir con Alan qué PCB pulir primero: colocación de la principal y tamaño de la de sensores (R01) suelen ser lo que más cambia el resto.
3. Cambiar colocación en `generar_pcb.py` → `--sin-ruteo` → revisar solapes → ruteo → DRC KiCad 7 → exportar fabricación → copiar a la PC de Alan (ruta de salida nueva) → DRC/ERC con MCP KiCad 10.
4. Cada cambio: commit local con la atribución vigente; **sin push** hasta que Alan lo autorice explícitamente.
5. Actualizar `pendientes-por-confirmar.md` (sin borrar IDs; historial en `docs/historial/`).

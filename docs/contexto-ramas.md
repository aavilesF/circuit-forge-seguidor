# Contexto para chats independientes (rama `engineering/robot-casero`, 5 nov 2026)

Pega el bloque que corresponda al abrir un chat nuevo. Reglas comunes: responder en español, no inventar medidas (marcarlas en
`docs/pendientes-por-confirmar.md`), commits pequeños en español, solo en la rama `engineering/robot-casero`, y respetar el reglamento
(caja 200 × 100 mm, 500 g, sin comunicación inalámbrica en competencia, el robot no se mueve antes de la señal, cambios al reglamento el 18 nov).

## A. Diseño en AutoCAD (`mecanica/autocad/`)
- Qué hay: `parametros.yaml` (fuente de verdad con estado y ID de pendiente), `generar_dxf.py`, `verificar_dxf.py`, `placa_{acrilico,mdf,pla}.dxf`, `placa_acrilico.png`, `NOTAS.md`.
- Diseño: placa plana de 192 × 97 mm, x de −72 a 120 (origen en el eje de las ruedas, X al frente, Y a la izquierda), muescas para ruedas de 34 mm, hueco de 34 mm y 4 agujeros para un ventilador 4010 entre la placa y las PCB, 8 agujeros M3 para las 2 PCB (salen de `electronica/kicad/*/*_mecanica.json`), ranuras de cinchos (2 por motor y 2 para la LiPo) y 2 agujeros de rueda loca.
- Peso estimado de la placa sola: acrílico 3 mm ≈ 59 g, MDF ≈ 38 g, PLA macizo ≈ 62 g.
- Verificado: auditoría ezdxf, mm, capas, polilíneas cerradas, conjunto dentro de 200 × 100, márgenes de agujeros ≥ 2 × espesor, piezas fantasma sin choques.
- Pendiente (todo `nominal` o `pendiente`): espesor de acrílico (3 mm propuesto, C01), kerf y holgura FDM (C05), medidas del motor N20 (M05–M07), LiPo (M14), ventilador (M21), rueda loca, y las PCB (M01–M20). **No cortar hasta confirmarlas.**
- Riesgos: R01 (el ventilador queda bajo las PCB, salida de aire limitada), R04 (caja de 200 × 100 incluye ruedas y sensores).
- Siguiente: confirmar medidas con regla/vernier, actualizar `parametros.yaml`, regenerar, hacer pieza de prueba, soporte del ventilador/falda en 3D (STEP/STL).

## B. Diagrama y PCB en KiCad (`electronica/kicad/`) — actualizado 11 nov (V7)
- Qué hay: `principal/` (ESP32 + DRV8833 + 2 MP1584 + ventilador + botones + medición de batería; 90 × 106 mm) y `sensores/` (12 × TCRT5000 montados abajo + módulo 74HC4067 + interruptor de emisores con 2N2222; 94 × 75 mm), cada una con `.kicad_sch`, `.kicad_pcb`, `.kicad_pro`, `fp-lib-table`, `*_drc.rpt` y la carpeta `fabricacion/` (PDF 1:1 de las dos caras, mapa de perforaciones, CSV); `robot_casero.pretty` (huellas propias; las de módulos siguen provisionales); `herramientas/` (`generar_principal.py`, `generar_sensores.py`, `generar_pcb.py`, `ruteador.py`, `huellas_propias.py`, `exportar_fabricacion.py`, `verificar_esquematico.py`); `pines_robot_casero.h`; `NOTAS.md`; `FABRICACION_CASERA.md`.
- Pines ESP32: mux S0=25, S1=26, S2=27, S3=33, SIG=34 (ADC1), emisores=13; motores AIN1=19, AIN2=21, BIN1=22, BIN2=23, SLEEP=16; ventilador=17; START=4, CAL=14; batería=36 (divisor 100k/33k).
- Las dos PCB son de **doble cara** (D18): vías de 1.8/0.8 mm que se rellenan con alambre soldado (no hay metalizado). Ruteo completo: 0 conexiones faltantes en ambas (sensores 37 vías, principal 29).
- Verificado: esquemáticos con netlist de KiCad 7.0.11 y ERC propio (0 errores); DRC de pcbnew 7: 0 errores en ambas (solo avisos de serigrafía); ERC/DRC de KiCad 10 por el servidor MCP del usuario: sensores 0 errores (informes JSON en la PC de Alan). Ninguna prueba eléctrica real.
- Pendiente para pasar a "lista para fabricar" (D): confirmar huellas provisionales M17 (pines del mux), M19/M20 (TCRT5000), M33 (agujeros MP1584) y regenerar.
- Cuidado: ajustar los MP1584 a 5.0 V y 6.0 V con multímetro antes de conectar cargas.


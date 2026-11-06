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

## B. Diagrama y PCB en KiCad (`electronica/kicad/`)
- Qué hay: `principal/` (ESP32 + DRV8833 + 2 MP1584 + ventilador + botones + medición de batería) y `barra_sensores/` (12 × TCRT5000 + módulo 74HC4067 + interruptor de emisores con 2N2222), cada una con `.kicad_sch`, `.kicad_pcb`, `.kicad_pro`, `fp-lib-table`, `*_drc.rpt`, `vista_*.png`; `robot_casero.pretty` (huellas propias provisionales); `herramientas/` (generadores `generar_principal.py`, `generar_barra.py`, `generar_pcb.py`, `ruteador.py`, `huellas_propias.py`, `verificar_esquematico.py`); `pines_robot_casero.h` (fuente de verdad de los pines); `NOTAS.md`.
- Pines ESP32: mux S0=25, S1=26, S2=27, S3=33, SIG=34 (ADC1), emisores=13; motores AIN1=19, AIN2=21, BIN1=22, BIN2=23, SLEEP=16; ventilador=17; START=4, CAL=14; batería=36 (divisor 100k/33k).
- Verificado: esquemáticos con netlist de KiCad 7.0.11 y ERC propio (0 errores). PCB con el **DRC oficial de pcbnew: 0 errores** y todas las redes unidas, solo avisos de serigrafía (y 2 `lib_footprint_mismatch` en la barra, 1 `track_dangling` en la principal).
- NO verificado: **ERC oficial** de KiCad (KiCad 7 no lo trae por línea de comandos: abrir en KiCad y correrlo), ninguna prueba eléctrica real.
- Ruteo con enrutador propio (Freerouting no se pudo ejecutar). Las pistas ROJAS (capa superior) son **puentes de alambre** que no se graban: ~22 en la barra y ~27 en la principal (R02).
- Pendiente: medidas reales de módulos (M01–M20), orden de pines del DRV8833 y del módulo del multiplexor, medición del diodo 1N5822, pulir la colocación para bajar puentes.
- Cuidado: ajustar los MP1584 a 5.0 V y 6.0 V con multímetro antes de conectar cargas.

# Medidas usadas por el chasis (generado por generar_chasis.py; no editar a mano)

Rama `seguidor-caseroV2`, commit base `6a83493eb82d1098cb2cdc24ca1f19619928c20d`. Editar `herramientas/parametros.py` y regenerar.

| Clave | Valor | Clase | Fuente |
|---|---|---|---|
| `caja_largo` | 200.0 | **DOCUMENTADO** | docs/requisitos.md (caja 20 x 10 cm, largo) |
| `caja_ancho` | 100.0 | **DOCUMENTADO** | docs/requisitos.md (caja 20 x 10 cm, ancho) |
| `altura_max` | — | **DOCUMENTADO** | docs/requisitos.md: "Sin límite de altura" |
| `peso_max` | 500.0 | **DOCUMENTADO** | docs/requisitos.md: 500 g en todo momento |
| `llanta_diam` | 26.7 | **REAL MEDIDO** | M08, vernier Alan 11 nov |
| `llanta_ancho` | 21.7 | **REAL MEDIDO** | M08, vernier Alan 11 nov |
| `rin_ancho` | 22.1 | **REAL MEDIDO** | M08, vernier Alan 11 nov (manda sobre la llanta para el ancho) |
| `motor_largo` | 24.5 | **REAL MEDIDO** | M05, vernier sobre un N20 equivalente (11 nov); sin terminales |
| `motor_seccion` | 12.0 x 10.0 | **REAL MEDIDO** | M06, vernier sobre N20 equivalente: 12 x 10 mm |
| `eje_sobresale` | 8.5 | **REAL MEDIDO** | M05 / D-V2-11 |
| `soporte_sep_agujeros` | 19.5 | **REAL MEDIDO** | M31, vernier Alan: 19.5 mm entre agujeros |
| `soporte_espesor` | 1.5 | **REAL MEDIDO** | M31, vernier Alan |
| `soporte_ancho_alto` | 25.0 x 11.0 | **DOCUMENTADO** | Ficha UNIT (docs/faltantes-unit.md): ABS 25 mm de ancho, 11 mm de alto, 1.33 g, 2 tornillos M2x7 + 2 tuercas |
| `soporte_largo` | — | **DESCONOCIDO** | Largo a lo largo del motor sin fuente (parametros.yaml histórico: 14 SIN FUENTE) |
| `h_eje` | 5.0 | **ESTIMADO** | Mitad del alto del motor (10/2) suponiendo motor apoyado directo en la base. MEDIR (V1) |
| `hueco_motores` | — | **DESCONOCIDO** | P-V2-34: separación entre las colas de los dos motores con terminales y cable soldado. MEDIR (V2) |
| `hueco_rin` | — | **DESCONOCIDO** | P-V2-34: hueco entre la cara del reductor y la cara interior del rin. MEDIR (V2) |
| `loca_caja` | 22.0 x 16.0 x 15.0 | **DOCUMENTADO** | M30 ficha UNIT: 22 x 16 x 15 mm, 10 g |
| `loca_sep_agujeros` | 15.0 | **DOCUMENTADO** | M30 ficha UNIT: "a ~15 mm" (aproximado) |
| `loca_h_montaje` | 15.0 | **ESTIMADO** | R03 abierto: se usa el alto total de la ficha como distancia cara de montaje-fondo de la esfera. MEDIR (V3) |
| `loca_agujero_d` | — | **DESCONOCIDO** | Diámetro de los 2 agujeros de la rueda loca. MEDIR (V3) |
| `vent_caja` | 40.0 x 40.0 x 10.0 | **DOCUMENTADO** | M21 ficha UNIT 40 x 40 x 10 |
| `vent_agujeros` | 32.0 x 3.2 | **DOCUMENTADO** | M21 dibujo UNIT: 4 x Ø3.2 ±0.2 en cuadrado de 32 ±0.3 |
| `vent_peso` | 15.0 | **REAL MEDIDO** | v2/inventario.csv: pesado 15 g el 13 nov |
| `vent_toma_d` | 34.0 | **DOCUMENTADO** | Diseño histórico mecanica/autocad/parametros.yaml (hueco_mm: 34); decisión de diseño, no medida |
| `kcd1` | 18.8 x 6.7 x 16.5 x 25.0 | **REAL MEDIDO** | M27 vernier: 18.8 x 6.7 mm; 16.5 alto sin terminales, 25 con terminales. No dice si 18.8 x 6.7 es el bisel o el cuerpo (V4) |
| `lipo` | — | **DESCONOCIDO** | M14: LiPo 2S 450-500 mAh por comprar; 61 x 16 x 15 / 30 g es solo referencia (Tattu 450) |
| `pcb_principal` | 96.0 x 74.0 | **EXTRAÍDO DE CAD** | v2/electronica/principal/principal.kicad_pcb, Edge.Cuts |
| `pcb_sensores` | 96.0 x 59.0 | **EXTRAÍDO DE CAD** | v2/electronica/sensores/sensores.kicad_pcb, Edge.Cuts (frente en arco R 103.0) |
| `pcb_espesor` | 1.6 | **EXTRAÍDO DE CAD** | (general (thickness 1.6)) de los .kicad_pcb; la fenólica real no está medida (V10) |
| `tcrt_alto` | 7.0 | **DOCUMENTADO** | M18 datasheet Vishay 10.2 x 5.8 x 7 |
| `tcrt_altura_piso` | 2.5 | **DOCUMENTADO** | Objetivo de diseño histórico (D05, parametros.yaml: altura_al_piso_mm 2.5; C.9 "lee mejor a ~2.5 mm") |
| `tcrt_separacion_cuerpo` | 0.0 | **ESTIMADO** | Se supone el cuerpo del TCRT5000 pegado a la PCB. MEDIR (V5) |
| `alto_max_sensores_arriba` | — | **DESCONOCIDO** | Pieza más alta en la cara de arriba de la placa de sensores (mux sobre tira hembra, J1 con conector). MEDIR (V6) |
| `tira_hembra_alto` | — | **DESCONOCIDO** | Altura de la tira hembra (bajo ESP32 y MP1584 queda la cabeza de un tornillo). MEDIR (V7) |
| `kit_separadores` | 6 x 10 x 15 x 20 | **DOCUMENTADO** | docs/diagnostico-mecanico.md X4 (kit trae 6/10/15/20 mm); P-V2-26: macho-hembra, ~1 g c/u |
| `separador_hex` | 5.5 | **ESTIMADO** | Hexágono M3 típico de 5.5 mm entre caras (esquina 3.18). MEDIR (V8) |
| `tuerca_m3` | 5.5 x 2.4 | **ESTIMADO** | Tuerca M3 típica 5.5 entre caras x 2.4 alto. MEDIR (V8) |
| `cabeza_m3_alto` | 3.0 | **ESTIMADO** | Cabeza de tornillo M3 típica <= 3 mm. MEDIR (V8) |
| `m3_libre` | 3.2 | **DOCUMENTADO** | E08: broca 3.2 mm para M3; dibujo UNIT del ventilador Ø3.2 |
| `acrilico_espesor` | 3.0 | **DOCUMENTADO** | Instrucción del equipo (17 nov) y C01 |
| `acrilico_densidad` | 1.19 | **ESTIMADO** | PMMA nominal 1.18-1.19 g/cm3 |
| `kerf` | — | **DESCONOCIDO** | Equipo, 17 nov: "No lo sé todavía". Medir con prueba_kerf.dxf |

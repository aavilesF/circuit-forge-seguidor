"""Parámetros del chasis final (rama seguidor-caseroV2). Fuente única de los números que usa generar_chasis.py.

Clases de cada medida (pedidas por el equipo):
  REAL MEDIDO      medido con vernier/báscula por el equipo (se cita el ID del repositorio)
  DOCUMENTADO      ficha del vendedor, hoja de datos, reglamento o decisión registrada en el repositorio
  EXTRAÍDO DE CAD  leído de los .kicad_pcb vigentes de v2/electronica (no medido en la pieza real)
  ESTIMADO         valor típico o deducido; NO sirve para declarar una pieza apta
  DESCONOCIDO      no hay dato en el repositorio; se pide medirlo

Para actualizar tras medir: cambiar 'valor' y 'clase' aquí y volver a ejecutar generar_chasis.py y verificar_chasis.py.
"""

M = {
    # ---------------- Reglamento ----------------
    'caja_largo':      dict(valor=200.0, clase='DOCUMENTADO', fuente='docs/requisitos.md (caja 20 x 10 cm, largo)'),
    'caja_ancho':      dict(valor=100.0, clase='DOCUMENTADO', fuente='docs/requisitos.md (caja 20 x 10 cm, ancho)'),
    'altura_max':      dict(valor=None,  clase='DOCUMENTADO', fuente='docs/requisitos.md: "Sin límite de altura"'),
    'peso_max':        dict(valor=500.0, clase='DOCUMENTADO', fuente='docs/requisitos.md: 500 g en todo momento'),

    # ---------------- Ruedas y motores ----------------
    'llanta_diam':     dict(valor=26.7, clase='REAL MEDIDO', fuente='M08, vernier Alan 11 nov'),
    'llanta_ancho':    dict(valor=21.7, clase='REAL MEDIDO', fuente='M08, vernier Alan 11 nov'),
    'rin_ancho':       dict(valor=22.1, clase='REAL MEDIDO', fuente='M08, vernier Alan 11 nov (manda sobre la llanta para el ancho)'),
    'motor_largo':     dict(valor=24.5, clase='REAL MEDIDO', fuente='M05, vernier sobre un N20 equivalente (11 nov); sin terminales'),
    'motor_seccion':   dict(valor=(12.0, 10.0), clase='REAL MEDIDO', fuente='M06, vernier sobre N20 equivalente: 12 x 10 mm'),
    'eje_sobresale':   dict(valor=8.5, clase='REAL MEDIDO', fuente='M05 / D-V2-11'),
    'soporte_sep_agujeros': dict(valor=19.5, clase='REAL MEDIDO', fuente='M31, vernier Alan: 19.5 mm entre agujeros'),
    'soporte_espesor': dict(valor=1.5, clase='REAL MEDIDO', fuente='M31, vernier Alan'),
    'soporte_ancho_alto': dict(valor=(25.0, 11.0), clase='DOCUMENTADO', fuente='Ficha UNIT (docs/faltantes-unit.md): ABS 25 mm de ancho, 11 mm de alto, 1.33 g, 2 tornillos M2x7 + 2 tuercas'),
    'soporte_largo':   dict(valor=None, clase='DESCONOCIDO', fuente='Largo a lo largo del motor sin fuente (parametros.yaml histórico: 14 SIN FUENTE)'),
    'h_eje':           dict(valor=5.0, clase='ESTIMADO', fuente='Mitad del alto del motor (10/2) suponiendo motor apoyado directo en la base. MEDIR (V1)'),
    'hueco_motores':   dict(valor=None, clase='DESCONOCIDO', fuente='P-V2-34: separación entre las colas de los dos motores con terminales y cable soldado. MEDIR (V2)'),
    'hueco_rin':       dict(valor=None, clase='DESCONOCIDO', fuente='P-V2-34: hueco entre la cara del reductor y la cara interior del rin. MEDIR (V2)'),

    # ---------------- Rueda loca ----------------
    'loca_caja':       dict(valor=(22.0, 16.0, 15.0), clase='DOCUMENTADO', fuente='M30 ficha UNIT: 22 x 16 x 15 mm, 10 g'),
    'loca_sep_agujeros': dict(valor=15.0, clase='DOCUMENTADO', fuente='M30 ficha UNIT: "a ~15 mm" (aproximado)'),
    'loca_h_montaje':  dict(valor=15.0, clase='ESTIMADO', fuente='R03 abierto: se usa el alto total de la ficha como distancia cara de montaje-fondo de la esfera. MEDIR (V3)'),
    'loca_agujero_d':  dict(valor=None, clase='DESCONOCIDO', fuente='Diámetro de los 2 agujeros de la rueda loca. MEDIR (V3)'),

    # ---------------- Ventilador ----------------
    'vent_caja':       dict(valor=(40.0, 40.0, 10.0), clase='DOCUMENTADO', fuente='M21 ficha UNIT 40 x 40 x 10'),
    'vent_agujeros':   dict(valor=(32.0, 3.2), clase='DOCUMENTADO', fuente='M21 dibujo UNIT: 4 x Ø3.2 ±0.2 en cuadrado de 32 ±0.3'),
    'vent_peso':       dict(valor=15.0, clase='REAL MEDIDO', fuente='v2/inventario.csv: pesado 15 g el 13 nov'),
    'vent_toma_d':     dict(valor=34.0, clase='DOCUMENTADO', fuente='Diseño histórico mecanica/autocad/parametros.yaml (hueco_mm: 34); decisión de diseño, no medida'),

    # ---------------- Interruptor ----------------
    'kcd1':            dict(valor=(18.8, 6.7, 16.5, 25.0), clase='REAL MEDIDO', fuente='M27 vernier: 18.8 x 6.7 mm; 16.5 alto sin terminales, 25 con terminales. No dice si 18.8 x 6.7 es el bisel o el cuerpo (V4)'),

    # ---------------- Batería ----------------
    'lipo':            dict(valor=None, clase='DESCONOCIDO', fuente='M14: LiPo 2S 450-500 mAh por comprar; 61 x 16 x 15 / 30 g es solo referencia (Tattu 450)'),

    # ---------------- PCB ----------------
    'pcb_principal':   dict(valor=(96.0, 74.0), clase='EXTRAÍDO DE CAD', fuente='v2/electronica/principal/principal.kicad_pcb, Edge.Cuts'),
    'pcb_sensores':    dict(valor=(96.0, 59.0), clase='EXTRAÍDO DE CAD', fuente='v2/electronica/sensores/sensores.kicad_pcb, Edge.Cuts (frente en arco R 103.0)'),
    'pcb_espesor':     dict(valor=1.6, clase='EXTRAÍDO DE CAD', fuente='(general (thickness 1.6)) de los .kicad_pcb; la fenólica real no está medida (V10)'),
    'tcrt_alto':       dict(valor=7.0, clase='DOCUMENTADO', fuente='M18 datasheet Vishay 10.2 x 5.8 x 7'),
    'tcrt_altura_piso': dict(valor=2.5, clase='DOCUMENTADO', fuente='Objetivo de diseño histórico (D05, parametros.yaml: altura_al_piso_mm 2.5; C.9 "lee mejor a ~2.5 mm")'),
    'tcrt_separacion_cuerpo': dict(valor=0.0, clase='ESTIMADO', fuente='Se supone el cuerpo del TCRT5000 pegado a la PCB. MEDIR (V5)'),
    'alto_max_sensores_arriba': dict(valor=None, clase='DESCONOCIDO', fuente='Pieza más alta en la cara de arriba de la placa de sensores (mux sobre tira hembra, J1 con conector). MEDIR (V6)'),
    'tira_hembra_alto': dict(valor=None, clase='DESCONOCIDO', fuente='Altura de la tira hembra (bajo ESP32 y MP1584 queda la cabeza de un tornillo). MEDIR (V7)'),

    # ---------------- Tornillería ----------------
    'kit_separadores': dict(valor=(6, 10, 15, 20), clase='DOCUMENTADO', fuente='docs/diagnostico-mecanico.md X4 (kit trae 6/10/15/20 mm); P-V2-26: macho-hembra, ~1 g c/u'),
    'separador_hex':   dict(valor=5.5, clase='ESTIMADO', fuente='Hexágono M3 típico de 5.5 mm entre caras (esquina 3.18). MEDIR (V8)'),
    'tuerca_m3':       dict(valor=(5.5, 2.4), clase='ESTIMADO', fuente='Tuerca M3 típica 5.5 entre caras x 2.4 alto. MEDIR (V8)'),
    'cabeza_m3_alto':  dict(valor=3.0, clase='ESTIMADO', fuente='Cabeza de tornillo M3 típica <= 3 mm. MEDIR (V8)'),
    'm3_libre':        dict(valor=3.2, clase='DOCUMENTADO', fuente='E08: broca 3.2 mm para M3; dibujo UNIT del ventilador Ø3.2'),

    # ---------------- Material ----------------
    'acrilico_espesor': dict(valor=3.0, clase='DOCUMENTADO', fuente='Instrucción del equipo (17 nov) y C01'),
    'acrilico_densidad': dict(valor=1.19, clase='ESTIMADO', fuente='PMMA nominal 1.18-1.19 g/cm3'),
    'kerf':            dict(valor=None, clase='DESCONOCIDO', fuente='Equipo, 17 nov: "No lo sé todavía". Medir con prueba_kerf.dxf'),
}

def v(k):
    return M[k]['valor']

# ---------------- Decisiones de diseño (no son medidas de componentes) ----------------
D = dict(
    t=v('acrilico_espesor'),
    x_base_trasera=2.5,      # borde trasero de la base (margen 2.5 mm a la caja)
    x_eje_desde_base=14.0,   # eje de ruedas 14 mm delante del borde trasero de la base
    holgura_rueda=2.0,       # entre llanta y acrílico (en planta) y por encima de la llanta
    base_ancho_ruedas=23.5,  # medio ancho de la base entre las ruedas (muesca)
    medio_ancho=48.0,        # medio ancho de base y tapa (96 mm)
    medio_ancho_brazo=49.0,  # brazo 98 mm (lleva los agujeros de la placa de sensores cerca del borde)
    m2_ranura=2.4,           # ranura para M2 (holgura media ISO 273)
    ranura_y=(4.0, 20.5),    # extensión en |y| de las ranuras de los soportes de motor (absorbe P-V2-34)
    cincho=(3.0, 12.0),      # ranuras para cincho/velcro de la batería (ancho x largo)
    x_pcb_principal=5.0,     # borde trasero de la PCB principal
    x_frente_sensores=197.0, # punta del arco de la placa de sensores
    L_base_tapa=20,          # separador base-tapa (kit)
    L_tapa_pcb=6,            # separador tapa-PCB principal (kit)
    L_brazo_sensores=20,     # separador brazo-placa de sensores (kit)
    cobre_libre=3.7,         # radio sin cobre alrededor de cada agujero nuevo en PCB (esquina del hexágono 3.18 + 0.5)
    web_min=2.0,             # material mínimo entre cortes y al borde (acrílico)
)

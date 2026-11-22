# Verificación del chasis (generado por verificar_chasis.py; no editar a mano)

Rama `seguidor-caseroV2`, commit base `6a83493eb82d1098cb2cdc24ca1f19619928c20d`. Kerf: PENDIENTE (geometría nominal).

| Pieza | Estado | Falta para APTO PARA CORTE |
|---|---|---|
| `base.dxf` | **PROVISIONAL** | PENDIENTE DE KERF; V1 altura del eje (fija la altura de la tapa; no cambia el DXF); V2 ancho con ruedas (legalidad; no cambia el DXF); V9 posición de los agujeros del soporte N20 (las ranuras cubren y = ±4 a ±20.5 mm) |
| `tapa.dxf` | **PROVISIONAL** | PENDIENTE DE KERF; Taladrar H1-H3 en la PCB principal con la plantilla (autorizado 17 nov); V7 tira hembra (cabeza de tornillo bajo ESP32 y U2) |
| `brazo_sensores.dxf` | **PROVISIONAL** | PENDIENTE DE KERF; V4 recorte del KCD1 (bisel o cuerpo); V3 rueda loca: agujeros (Ø y separación) y altura de montaje; Taladrar S1-S2 en la PCB de sensores; V5/V6 altura de los TCRT y de la pieza más alta de la placa de sensores |

Peso ESTIMADO: 303 g · centro de masa ESTIMADO x = 69.4 mm, z = 23.0 mm · carga en la rueda loca ≈ 145 g

## Errores (0)
- ninguno

## Avisos y pendientes (no son validación física) (7)
- ! **PCB principal**: H2 cae bajo el cuerpo de A1 (módulo sobre tira hembra): la cabeza del tornillo debe caber debajo (medir V7) y se atornilla antes de enchufar el módulo
- ! **PCB principal**: H3 cae bajo el cuerpo de U2 (módulo sobre tira hembra): la cabeza del tornillo debe caber debajo (medir V7) y se atornilla antes de enchufar el módulo
- ! **PCB sensores**: S1: solo 2.65 mm de material al borde de la fenólica; taladrar con piloto y sin presionar
- ! **PCB sensores**: S1 a 3.11 mm del contorno de Q1: orientar una cara plana del hexágono del separador hacia Q1
- ! **ensamble**: ANCHO CON RUEDAS SIN VERIFICAR: = (G/2 + 24.5 + hueco + 22.1) x 2. Cumple 100 mm solo si G + 2·hueco <= 6.8 mm (G = separación entre colas de motor con terminales y cable; hueco = reductor-rin). Con G=4 y hueco=0.5 (ESTIMADOS) da 98.2 mm. Medir V2 (P-V2-34)
- ! **ensamble**: lente de los TCRT5000 a 2.75 mm del piso (objetivo documentado 2.5 mm); depende de V1, V5 y del separador del brazo
- ! **anidado**: tamaño real de la lámina sin confirmar (el equipo no lo sabe): comprobar antes de cortar

## Comprobado en archivos (71)
- ✓ **base.dxf**: abre con ezdxf y la auditoría no encuentra errores
- ✓ **base.dxf**: unidades: milímetros ($INSUNITS=4, $MEASUREMENT=1), escala 1:1
- ✓ **base.dxf**: solo capas CORTE y GRABADO
- ✓ **base.dxf**: 18 contornos de corte, todos cerrados
- ✓ **base.dxf**: sin entidades duplicadas
- ✓ **base.dxf**: material mínimo: 2.90 mm al borde, 2.55 mm entre cortes (mín. pedido 2.0 mm), sin superposiciones
- ✓ **base.dxf**: medidas exteriores 100.50 x 96.00 mm coinciden con el diseño
- ✓ **base.dxf**: 28 trazos de grabado dentro de la pieza y a >= 0.5 mm de los cortes
- ✓ **tapa.dxf**: abre con ezdxf y la auditoría no encuentra errores
- ✓ **tapa.dxf**: unidades: milímetros ($INSUNITS=4, $MEASUREMENT=1), escala 1:1
- ✓ **tapa.dxf**: solo capas CORTE y GRABADO
- ✓ **tapa.dxf**: 11 contornos de corte, todos cerrados
- ✓ **tapa.dxf**: sin entidades duplicadas
- ✓ **tapa.dxf**: material mínimo: 2.90 mm al borde, 4.42 mm entre cortes (mín. pedido 2.0 mm), sin superposiciones
- ✓ **tapa.dxf**: medidas exteriores 89.50 x 96.00 mm coinciden con el diseño
- ✓ **tapa.dxf**: 30 trazos de grabado dentro de la pieza y a >= 0.5 mm de los cortes
- ✓ **brazo_sensores.dxf**: abre con ezdxf y la auditoría no encuentra errores
- ✓ **brazo_sensores.dxf**: unidades: milímetros ($INSUNITS=4, $MEASUREMENT=1), escala 1:1
- ✓ **brazo_sensores.dxf**: solo capas CORTE y GRABADO
- ✓ **brazo_sensores.dxf**: 10 contornos de corte, todos cerrados
- ✓ **brazo_sensores.dxf**: sin entidades duplicadas
- ✓ **brazo_sensores.dxf**: material mínimo: 3.65 mm al borde, 4.88 mm entre cortes (mín. pedido 2.0 mm), sin superposiciones
- ✓ **brazo_sensores.dxf**: medidas exteriores 80.00 x 98.00 mm coinciden con el diseño
- ✓ **brazo_sensores.dxf**: 32 trazos de grabado dentro de la pieza y a >= 0.5 mm de los cortes
- ✓ **prueba_kerf.dxf**: abre con ezdxf y la auditoría no encuentra errores
- ✓ **prueba_kerf.dxf**: unidades: milímetros ($INSUNITS=4, $MEASUREMENT=1), escala 1:1
- ✓ **prueba_kerf.dxf**: solo capas CORTE y GRABADO
- ✓ **prueba_kerf.dxf**: 7 contornos de corte, todos cerrados
- ✓ **prueba_kerf.dxf**: sin entidades duplicadas
- ✓ **prueba_kerf.dxf**: material mínimo: 3.30 mm al borde, 4.00 mm entre cortes (mín. pedido 2.0 mm), sin superposiciones
- ✓ **prueba_kerf.dxf**: medidas exteriores 60.00 x 30.00 mm coinciden con el diseño
- ✓ **prueba_kerf.dxf**: 5 trazos de grabado dentro de la pieza y a >= 0.5 mm de los cortes
- ✓ **PCB**: v2/electronica/principal/principal.kicad_pcb: md5 a9066741539c3da935c77b6cd58d9cb3 = el del DRC aprobado (registro_drc.json)
- ✓ **PCB**: v2/electronica/sensores/sensores.kicad_pcb: md5 fc65e738860c76cf061ef9a5f05144f7 = el del DRC aprobado (registro_drc.json)
- ✓ **PCB**: mapeo KiCad -> robot es un giro de -90° sin espejo (cara de componentes hacia arriba)
- ✓ **PCB principal**: H1 (KiCad 191.0, 74.0): cobre libre 10.82 mm (mín. 3.7; más cercano: pad U3); 3.90 mm de material al borde
- ✓ **tapa.dxf**: agujero Ø3.2 de H1 en (73.00, -42.50) recalculado desde KiCad
- ✓ **PCB principal**: H2 (KiCad 148.0, 132.5): cobre libre 5.76 mm (mín. 3.7; más cercano: pista B.Cu); 7.90 mm de material al borde
- ✓ **tapa.dxf**: agujero Ø3.2 de H2 en (14.50, 0.50) recalculado desde KiCad
- ✓ **PCB principal**: H3 (KiCad 112.0, 104.5): cobre libre 6.93 mm (mín. 3.7; más cercano: pista F.Cu); 9.90 mm de material al borde
- ✓ **tapa.dxf**: agujero Ø3.2 de H3 en (42.50, 36.50) recalculado desde KiCad
- ✓ **PCB sensores**: S1 (KiCad 104.75, 122.75): cobre libre 4.20 mm (más cercano: pista F.Cu); 2.65 mm de material al borde
- ✓ **brazo_sensores.dxf**: agujero Ø3.2 de S1 en (149.75, 43.75) recalculado desde KiCad
- ✓ **PCB sensores**: S2 (KiCad 187.5, 120.0): cobre libre 4.90 mm (más cercano: pista B.Cu); 7.40 mm de material al borde
- ✓ **brazo_sensores.dxf**: agujero Ø3.2 de S2 en (152.50, -39.00) recalculado desde KiCad
- ✓ **tapa/PCB**: cabeza del tornillo B1 (r 2.75) a 3.28 mm del borde del pad más cercano de la PCB principal
- ✓ **tapa/PCB**: cabeza del tornillo B2 (r 2.75) a 6.18 mm del borde del pad más cercano de la PCB principal
- ✓ **base/tapa**: separador B1 (39.50, 43.50) coincide en base y tapa
- ✓ **base/tapa**: separador B2 (39.50, -43.50) coincide en base y tapa
- ✓ **base/tapa**: separador B3 (87.00, 43.50) coincide en base y tapa
- ✓ **tapa/brazo**: unión B3 coincide en tapa y brazo
- ✓ **base/tapa**: separador B4 (87.00, -43.50) coincide en base y tapa
- ✓ **tapa/brazo**: unión B4 coincide en tapa y brazo
- ✓ **tapa/brazo**: unión central J0 coincide
- ✓ **base.dxf**: ventilador: 4 x Ø3.2 en cuadrado de 32.0 mm (dibujo UNIT) y toma Ø34 centrada
- ✓ **base.dxf**: 4 ranuras M2 de los soportes en x = [6.75, 26.25] (eje 16.5, separación 19.5 medida)
- ✓ **ensamble**: largo total 194.50 mm (x de 2.50 a 197.00) <= 200 mm, contando ruedas, placas, tornillos y la placa de sensores
- ✓ **ensamble**: ancho de las placas de acrílico: 98.0 mm <= 100 mm
- ✓ **ensamble**: altura: el reglamento no limita la altura (docs/requisitos.md)
- ✓ **ensamble**: solo las ruedas y la rueda loca tocan el piso: lo más bajo es "TCRT5000 OP1" a 2.75 mm
- ✓ **ensamble**: sin choques entre 55 sólidos simplificados (ruedas, motores, soportes, batería máx., ventilador, separadores, tuercas, cabezas, PCB, TCRT, rueda loca, KCD1)
- ✓ **ensamble**: tapa 1.65 mm por encima de las llantas (con h_eje ESTIMADO 5.0 mm)
- ✓ **acceso**: START: libre por encima
- ✓ **acceso**: CAL: libre por encima
- ✓ **acceso**: RESET: libre por encima
- ✓ **acceso**: USB-C (enchufe, 30 mm hacia atrás): libre por encima
- ✓ **acceso**: KCD1: libre por encima
- ✓ **ensamble**: centro de masa ESTIMADO en x = 69.4 mm, entre el eje (16.5) y la rueda loca (127.0): apoyo en 3 puntos; ~52 % del peso en las ruedas
- ✓ **ensamble**: peso total ESTIMADO 303 g (límite 500 g; confirmar con báscula)
- ✓ **anidado**: las 4 piezas (5 mm entre piezas y al borde) caben en 325 x 108 mm en una fila, o en 200 x 196 mm en dos filas; caben en 300 x 300 y en 600 x 300
- ✓ **anidado**: vistas/anidado.png dibujada leyendo los 4 DXF (comprueba que se pueden abrir y dibujar)

## Lo que esta verificación NO comprueba
- Que las piezas reales midan lo nominal (falta el kerf y una pieza de prueba cortada).
- Resistencia mecánica, rigidez, vibración o comportamiento en la pista.
- Que los componentes reales coincidan con las fichas (alturas, agujeros de la rueda loca, recorte del KCD1).
- Alturas de los componentes de la PCB principal (no hay nada encima de ella, así que no limitan el diseño).

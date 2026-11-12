# Manual de ensamblaje, puesta en marcha y calibración — Speed Follower (PCB-chasis)

Referencias de piezas: [`BOM_FINAL.csv`](BOM_FINAL.csv). Planos: `hardware/electronics/pcba/` (vistas 2D/3D de la PCBA),
`hardware/electronics/fabricacion/ensamblaje_superior.pdf` e `ensamblaje_inferior.pdf`, `hardware/mechanical/planos/`
y `hardware/mechanical/render/`. Marco del robot: x hacia adelante desde el eje de las ruedas, y hacia la izquierda.

> Nada de este procedimiento se ha ejecutado todavía: no hay placa fabricada. Los pasos E1-E9 son las pruebas de
> aceptación del hardware real. Hasta completarlos, el robot **no está validado físicamente**.

## 0. Herramientas

Cautín de punta fina (o estación de aire caliente), flux, malla, pinzas, lupa o microscopio; multímetro; fuente de
laboratorio con límite de corriente (0-10 V, ≥ 1 A); llave Allen de 1.3 mm (M2 de botón); STLINK-V3MINIE con su cable
STDC14; cargador de LiPo 2S con balanceo; báscula de 0.1 g; dos básculas de cocina (reparto de peso).

## 1. Fabricación

| Pieza | Archivos | Especificación |
|---|---|---|
| PCB | `hardware/electronics/fabricacion/speed_follower_gerbers.zip` | Ver [`fabricacion/LEEME.md`](../hardware/electronics/fabricacion/LEEME.md): 4 capas, 1.6 mm, ENIG |
| Ensamblaje de la PCB (opcional, por el fabricante) | `bom_ensamblaje.csv`, `posiciones_superior.csv`, `posiciones_inferior.csv` | Ensamblaje en **ambas caras**. Los componentes de orificio pasante (J1, J4, SW1) se sueldan a mano |
| Impresión 3D | `hardware/mechanical/stl/` (6 piezas) | PA12 por MJF. Repasar los agujeros M2 con broca de 2.3 mm si quedan estrechos |

## 2. Ensamble de la PCBA (si se suelda a mano)

1. **Cara inferior primero** (queda abajo en el robot): los 16 sensores QRE1113GR (U11-U26), sus 32 resistencias
   (R20-R51: 75 Ω del emisor y 10 kΩ del fototransistor) y los pasivos inferiores (C20-C23 del DRV8833, R4 y C3 del
   divisor de batería). **Los sensores van con la ventana óptica hacia el piso** y el pin 1 (ánodo) hacia afuera del
   arco, como en la serigrafía inferior (S1 … S16).
2. **Cara superior**, en este orden: U1 (STM32G431CBT6, pin 1 según la serigrafía; revisar puentes con lupa), U3
   (DRV8833PWPR: **la almohadilla térmica debe soldarse**: estaño en la almohadilla y aire caliente), U2 (TPS563200)
   y L1, Q1-Q3, D1 (banda del cátodo hacia VBAT_SW), F1, pasivos, LEDs (D2 verde 3V3, D3 verde OK, D4 rojo ERR),
   botones SW2 START, SW3 CAL, SW4 RST, conectores J2 (ENC IZQ) y J3 (ENC DER) con sus pestañas soldadas.
3. **Orificio pasante al final**: J4 (STDC14, pin 1 marcado), SW1 (ON/OFF, actuador hacia el borde derecho) y J1 (XT30).
4. **J1 — comprobar el género antes de soldar.** J1 es **XT30UPB-M** (pines macho en la placa). La batería Tattu debe
   traer el conector **hembra** (XT30U-F). Si al recibir la batería trae otro género, **no soldar J1** y resolver antes
   (no improvisar un adaptador sin revisar la polaridad +/− que marca la serigrafía).
5. Limpiar el flux (alcohol isopropílico), sobre todo en el arco de sensores: el residuo cambia la reflectancia.

## 3. Pruebas eléctricas sin batería (E1-E4)

| Paso | Prueba | Criterio |
|---|---|---|
| E1 | Inspección visual con lupa: puentes en U1 (paso 0.5 mm) y U3, sensores orientados | Sin puentes; los 16 sensores con la ventana hacia abajo |
| E2 | Resistencia con el multímetro: TP1 (VBAT_SW)–GND, TP2 (+3V3)–GND, TP5 (+3V3A)–GND | Ninguna en corto (> 1 kΩ tras cargar los capacitores) |
| E3 | Fuente de laboratorio en J1 a **7.4 V con límite de 100 mA**, SW1 en ON | Corriente de reposo < 60 mA; D2 encendido; TP2 = 3.30 V ± 2 %; TP11 (VBAT_MED) ≈ 7.4 × 33/133 = 1.84 V |
| E4 | Polaridad invertida: fuente a −7.4 V en J1 (límite 100 mA) | Corriente ≈ 0; nada se calienta (Q1/Q2 bloquean). Volver a la polaridad correcta |

## 4. Programación (E5)

1. Conectar el STLINK-V3MINIE a J4 con el cable STDC14 (pin 1 del cable plano, hilo de color, hacia el "1" de la
   serigrafía). La placa se alimenta **de su fuente o batería**: el STLINK no la alimenta.
2. Compilar y grabar según [`firmware/README.md`](../firmware/README.md) (`make` y `make flash`, o STM32CubeProgrammer).
3. Abrir el puerto serie virtual a 115200 8N1. Escribir `?`: debe responder la ayuda. `p` muestra los parámetros.

**E5 aprobado si:** el MCU responde por la consola (al arrancar imprime si cargó parámetros y calibración de la flash) y
la línea `vbat` del comando `r` coincide con la tensión de la fuente ± 0.1 V. `t` activa/desactiva la telemetría a 50 Hz
(estado, error de línea, velocidad pedida, ciclos de PWM, velocidades de rueda y batería).

## 5. Sensores (E6)

Con `r` la consola imprime, por sensor, la lectura con los emisores apagados (`amb`), con los emisores encendidos
(`emi`), el rango de la calibración guardada y el valor normalizado (`osc`, 0 blanco … 1 negro); al final, `vbat` y los
contadores de los encoders. Con el robot sobre fórmica blanca y luego sobre la cinta negra:

- Cada sensor debe cambiar ≥ 150 cuentas entre blanco y negro (la calibración exige ese rango).
- La columna `amb` debe seguir a la luz del cuarto (tapar el robot con la mano la cambia) mientras la diferencia `amb − emi` se mantiene: confirma que la resta de luz ambiente funciona.
- **M8 (medición pendiente)**: registrar el ruido (desviación de 200 lecturas quietas), la diferencia blanco-negro a la
  altura real (3.05 mm) y el tiempo de establecimiento del fototransistor (si la diferencia crece al subir
  `T_EMISOR_US`, el valor de 200 µs [S] es corto). Llevar los valores a `config/robot_maestro.yaml` (`optica`).

## 6. Motores, encoders y cables

1. Soldar la tarjeta del encoder Pololu #4760 a las terminales de cada motor #3048 **antes** de montarlo, con el imán
   en el eje extendido. La tarjeta sobresale 2.8 mm de la sección del motor: **esa parte va hacia abajo** (hacia la PCB),
   con el conector hacia el centro del robot.
2. **Cable Pololu #4765 — continuidad pin 1 a pin 1** antes de conectarlo: el pin 1 es GND en la tarjeta del encoder y
   en J2/J3 (orden del conector en la placa: 1 GND, 2 B, 3 A, 4 VCC, 5 M2, 6 M1). Un cable cruzado aplica la tensión
   del motor al encoder.
3. Presionar cada llanta #1087 en el eje hasta que su cara exterior quede al ras del extremo del eje (quedan ≈ 2 mm
   libres contra la reductora).

## 7. Ensamble mecánico

1. **Soportes de motor** (por lado: base + tapa + 4 tornillos M2 × 12 + 4 tuercas): base sobre la cara superior de la
   PCB en el área marcada (zona sin componentes junto a cada rueda), motor encima con la reductora hacia afuera, tapa
   en U encima. Los tornillos entran **desde abajo** (cabeza bajo la PCB, a 3.4 mm del piso) y las tuercas quedan
   arriba de las pestañas de la tapa. Apretar parejo: la tapa sujeta al motor por presión, sin deformarlo.
2. **Rueda loca**: bola de 1/4 in en la carcasa (cara inferior, bajo el agujero de Ø 6.4 mm de la punta), tapa en la cara
   superior, 2 tornillos M2 × 8 **desde abajo** (la cabeza entra en la caja de la carcasa y queda al ras: nada sobresale
   hacia el piso) y tuercas sobre la tapa. La bola debe girar libre.
3. Conectar los cables de los encoders: motor izquierdo a J2 (ENC IZQ), derecho a J3 (ENC DER). Enrollar y amarrar el sobrante.
4. **Batería**: Dual Lock SJ3550 sobre las caras superiores de las dos tapas y en la cara inferior de la batería;
   batería transversal sobre los motores, cables por el lado derecho hacia J1.
5. **Reparto de peso (M2, M5)**: pesar el robot completo con batería (CAD: 112.9 g) y, con dos básculas (una bajo las
   dos ruedas, otra bajo la bola, a la misma altura), calcular x_CG = 92 mm × m_bola / m_total. **Criterio de aceptación:
   x_CG ≤ 25 mm** (CAD: 20.1 mm). Simulado: hasta 25 mm, 100 % de éxito; a 27 mm, 98.3 %; a 30 mm, 80 % (y el modo
   seguro no lo compensa). Si no se cumple, recorrer la batería hacia atrás sobre las tapas de los soportes.

## 8. Sentido de giro y encoders (E7) — con las ruedas en el aire

1. Robot sobre un soporte, ruedas sin tocar nada. Batería conectada, SW1 en ON, consola abierta.
2. `prueba 0.3 0`: la rueda **izquierda** debe girar 2 s **hacia adelante**. `prueba 0 0.3`: la **derecha**, hacia adelante.
3. Con `t` (telemetría) durante la prueba: la velocidad de la rueda que gira debe salir **positiva**.
4. Si un motor gira al revés, o su encoder cuenta negativo: cambiar `firmware.invertir_motor_izq/der` o
   `invertir_encoder_izq/der` en `config/robot_maestro.yaml`, correr `python3 herramientas/generar_config_firmware.py`,
   recompilar y grabar. (No se intercambian cables: el orden de pines es el del cable #4765.)
5. **M7 (medición crítica)**: con `prueba 1 1` (ciclo limitado a 0.5 por el firmware) y la batería llena, registrar la
   velocidad libre de los encoders. La corriente de bloqueo se mide aparte con la fuente de laboratorio (motor
   suelto, eje sujeto 1 s, a 7.4 V). Actualizar `motores.pololu_hpcb12_10` en el YAML si difieren más de 10 % de la ficha
   (3400 rpm, 0.75 A a 12 V) y volver a correr `python3 sim/fase_final.py F` antes de competir.

## 9. Calibración (regla C03) y primera vuelta (E8-E9)

1. Robot en la pista con la línea bajo el centro del arco de sensores. Pulsar **CAL**: D3 (OK) parpadea.
2. Durante ≤ 10 s **deslizar el robot a mano** de lado a lado sobre la línea (los motores no se mueven) para que los
   16 sensores vean blanco y negro. Pulsar **CAL** otra vez.
3. Si todos los sensores vieron un rango ≥ 150 cuentas, la calibración se guarda en la flash y D3 queda fijo (estado
   LISTO). Si no, el robot vuelve a ESPERA, D4 (ERR) parpadea y la consola lo indica: repetir con un barrido más amplio.
4. **E8 — modo seguro primero**: por la consola `modo seguro` y `w` (guardar). Colocar el robot en la línea y pulsar
   **START**. El robot sigue la pista con C3e a v_max 0.63 m/s. START otra vez lo detiene.
5. **E9 — modo competencia**: `modo comp` y `w`. Control C3m, v_max 0.8165 m/s (tiempo simulado 5.81 s en la pista
   de referencia). Si derrapa, bajar `set v_max 0.75` y subir de 0.02 en 0.02.
6. **M1** (μ): plano inclinado con la llanta sobre fórmica; actualizar `entorno.mu` en el YAML y revisar la tabla de
   v_max por μ de `docs/SIMULACION_DINAMICA.md`.

## 10. Indicadores y paros de seguridad

| Indicación | Significado |
|---|---|
| D2 verde | 3.3 V presentes |
| D3 OK fijo | Calibrado y listo / siguiendo la línea |
| D3 OK parpadeando | Calibrando |
| D4 ERR fijo | Estado ERROR: nFAULT del DRV8833, rueda trabada 0.3 s, lecturas imposibles de los sensores, o batería insuficiente al encender. Se sale con CAL |
| D4 ERR parpadeando | Calibración insuficiente, batería baja (< 6.8 V: START no arranca) o parada por línea perdida > 0.3 s o batería < 6.4 V sostenida. START o CAL vuelven a LISTO |

## 11. Desarmado

Batería: tirar del conector, no del cable. Motores: quitar los 4 tornillos de cada soporte (la PCB no se desuelda).
Bola: quitar las 2 tuercas de la tapa y bajar la carcasa. Programación: J4 queda accesible con la batería puesta.

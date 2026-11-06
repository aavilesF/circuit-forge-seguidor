# Robot casero · D. Manual de ensamblaje

Para Alan y Daniel. El orden va de lo más bajo y resistente al calor a lo más delicado: **resistencias y diodo → cerámicos → transistores y botones → headers → electrolíticos → cables → módulos**. Cada etapa termina con una prueba que se hace **antes** de pasar a la siguiente y **sin la LiPo**. La LiPo se conecta hasta la etapa 8.

**Documentos de apoyo:**

| Documento | Para qué |
|---|---|
| [`placa/PLANTILLA_PLACA_1a1.pdf`](placa/PLANTILLA_PLACA_1a1.pdf), hoja 1 (2:1) | Ver dónde va cada pieza |
| [`placa/PLANTILLA_PLACA_1a1.pdf`](placa/PLANTILLA_PLACA_1a1.pdf), hoja 2 (1:1) | Pistas, en espejo |
| [`CONEXIONES.md`](CONEXIONES.md) | Por qué va cada cosa |
| [`LAYOUT_PLACA.md`](LAYOUT_PLACA.md) | Coordenadas, corte de la placa y ataque con cloruro |
| [`firmware/robot-casero/README.md`](../../firmware/robot-casero/README.md) | Cargar el programa y usar la consola |

**Herramientas:**

- Cautín a 330–350 °C con punta fina.
- Soldadura y pasta para soldar (flux).
- Multímetro.
- **Pila de 9 V con su broche**: es la fuente de las pruebas. Una fuente de laboratorio con límite de 300 mA es aún mejor.
- Termofil (heat-shrink), pinzas y cúter.

> **Regla:** en placa fenólica el cobre se despega con calor de más. Cada punto lleva 2–3 s, con flux; si no fluye, se deja enfriar y se repite. Nunca jalen una pata con la soldadura caliente.

---

## Etapa 0 · Piezas sueltas (sin soldar nada, 30–40 min)

Anoten cada resultado en `docs/pendientes-por-confirmar.md` con su ID.

| # | Qué | Cómo | Debe dar | ID |
|---|---|---|---|---|
| 0.1 | **Ajustar MP1584 #1** | Pila de 9 V en IN+/IN−. Multímetro en OUT+/OUT−. Giren el trimmer (multivuelta; suelen venir altos: 10–20 vueltas antihorario). | **5.00 V** (4.95–5.10) | E01 |
| 0.2 | **Ajustar MP1584 #2** | Igual. | **6.00 V** (5.9–6.1) | E02 |
| 0.3 | Marcar los módulos | Plumón: "5V" y "6V". **No se vuelven a tocar los trimmers.** | — | — |
| 0.4 | Diodos 1N5822 | Modo diodo: roja al lado sin franja. | 0.15–0.30 V directa, OL inversa | E03 |
| 0.5 | Patas del 2N2222 | Modo diodo, roja en la pata del centro (B) y negra en cada lado: ~0.6–0.7 V en ambas. La B-E marca unos mV **más** que la B-C. Si el multímetro tiene zócalo hFE, úsenlo. Dibujen E-B-C con la cara plana al frente. | E y C identificadas | P05 |
| 0.6 | VIN del ESP32 | Solo USB conectado. Negra en GND y roja en el pin de la derecha junto al USB-C. | ~4.7–5 V = **VIN** | P07 |
| 0.7 | DRV8833 contra la plantilla | Pongan el módulo sobre la hoja 2 (1:1) **volteado como en la hoja 1**: IN1…IN4 hacia el ESP32. Las letras deben coincidir con las de la hoja 1 y los pines con las cruces. | Coinciden | M09, M10 |
| 0.8 | ESP32 contra la plantilla | Igual: 15 + 15 pines sobre las cruces, USB-C hacia arriba. | Coinciden | M01–M03 |
| 0.9 | Botones | Continuidad entre patas **en diagonal**: abierto suelto y cerrado al oprimir. | Abre y cierra | M26 |

Si 0.7 u 0.8 no coinciden, **paren y avisen**: hay que mover la huella antes de taladrar.

---

## Etapa 1 · Placa grabada y taladrada (sin piezas)

Sigan [`LAYOUT_PLACA.md`](LAYOUT_PLACA.md) §1–§3: cortar, dibujar, cloruro y taladrar.

**Pruebas con el multímetro en continuidad:**

| Entre | Debe dar | Si falla |
|---|---|---|
| VBAT (pad J1) y GND (pad J2) | **ABIERTO** | Raspen con cúter el puente de cobre |
| Riel VBAT (x = 0) y riel GND (x = 2), en 3 puntos | ABIERTO | Igual |
| Pad J1 y pad R1 (abajo a la izquierda) | Continuidad | Pista cortada: repasen con alambre |
| Pad VP del ESP32 (24,17) y pad R1 derecho (4,31) | Continuidad (la pista larga de la orilla) | Igual |
| Pines vecinos de J5 y de J6 | Abierto entre cada par | Raspen |
| Las 4 pistas de motor entre sí | Abierto | Raspen |

---

## Etapa 2 · Resistencias, diodo y cerámicos (lo más bajo)

| Orden | Pieza | Dónde | Cuidado |
|---|---|---|---|
| 1 | R1 100 kΩ (café-negro-amarillo) | (0,31)–(4,31) | Acostada. |
| 2 | R5 1 kΩ (café-negro-rojo) | (16,21)–(16,25) | Acostada y pegada a la placa (queda bajo el ESP32). |
| 3 | R2 33 kΩ (naranja-naranja-naranja) | (11,30)–(11,31) | Parada. |
| 4 | R4 1 kΩ | (29,6)–(30,6) | Parada. |
| 5 | **D2 1N5822** | (11,0)–(17,0) | **Franja hacia la derecha** (hacia el VIN). Agujeros de 1.3–1.5 mm. |
| 6 | C2, C5, C6 100 nF ("104") | ver hoja 1 | Sin polaridad. |

**Prueba 2:**

- R1 + R2 entre el pad J1 y el pad J2: **133 kΩ** ± 5 %.
- D2 en modo diodo: ~0.2 V con la roja en (11,0).
- Sigue sin haber continuidad VBAT–GND.

---

## Etapa 3 · Transistores y botones

| Orden | Pieza | Cuidado |
|---|---|---|
| 1 | Q1 2N2222 en (31,5)–(31,7) | **La pata E al pad E** (arriba), según lo medido en 0.5. Déjenlo a ~5 mm de la placa. |
| 2 | Q2 2N2222 en (18,24)–(18,26) | La pata E al pad E (abajo). |
| 3 | SW2 START y SW3 CAL | Las 4 patas soldadas (sujetan); solo 2 están conectadas. |

**Prueba 3 (multímetro en continuidad):**

| Botón | Entre | Suelto | Oprimido |
|---|---|---|---|
| START | Pad (15,24) y bus GND | Abierto | Cerrado |
| CAL | Pad (23,24) y bus GND | Abierto | Cerrado |

---

## Etapa 4 · Headers

**Truco de alineación:**

1. Inserten las tiras hembra **en el módulo** (ESP32 o DRV8833) y el módulo en la placa.
2. Suelden solo **2 pines de las esquinas**.
3. Saquen el módulo y suelden el resto.

Así quedan paralelos.

| Orden | Header | Dónde |
|---|---|---|
| 1 | 2 × hembra 1×15 (ESP32) | x = 14 y x = 24, de y = 4 a 18 |
| 2 | 2 × hembra 1×6 (DRV8833) | x = 5 y x = 11, de y = 13 a 18 |
| 3 | Macho 1×5 (J5), 1×8 (J6), 1×2 (J7) | x = 28 / (21,23)–(21,24) |

**Prueba 4:** continuidad del pin de cada header a su destino. Tabla en [`LAYOUT_PLACA.md` §5](LAYOUT_PLACA.md#5-tabla-de-conexiones-red--pines). Las más importantes:

| Del header del ESP32 | A |
|---|---|
| D19, D21, D22, D23 | IN1, IN2, IN3, IN4 del header del DRV8833 (en línea recta) |
| D16 | EEP |
| D27…VN | J6 A1…A8 |
| D13 | J5.LED_ON y R4 |
| 3V3 | J5.3V3 |
| VIN | J5.5V, J7.+ y el lado franja de D2 |
| GND | Bus GND |

**Pruebas de cortos** entre pines vecinos de cada tira: 3V3–GND, VIN–GND, VCC–GND del DRV8833 → todo **abierto**.

---

## Etapa 5 · Electrolíticos, cables y módulos de voltaje

| Orden | Pieza | Cuidado |
|---|---|---|
| 1 | C1 470 µF en (0,10)–(2,10) | La franja (−) va a la **derecha** (riel GND). **Un electrolítico al revés puede reventar.** |
| 2 | C4 470 µF en (8,22)–(10,22) | Franja (−) a la derecha. |
| 3 | Arnés de batería (fuera de la placa) | Rojo de la LiPo → **fusible** → **SW-104S** → **D1 1N5822** (franja hacia la placa) → cable 18 AWG a **J1**. Negro de la LiPo → cable 18 AWG a **J2**. Cada unión con termofil. Rojo para +, negro para −. |
| 4 | U2 (5 V) y U3 (6 V) | Cinta doble cara en su lugar (esquinas izquierdas). Cada terminal (IN+, IN−, OUT+, OUT−) se une a su pad con una pata de resistencia, **según las letras de la hoja 1**. Si sus terminales quedan en otro orden, crucen los alambres: lo que manda son las letras. |
| 5 | Motores a J3 (derecho) y J4 (izquierdo) | Todavía **no**: se sueldan en la etapa 7. |

**Prueba 5: primera alimentación, con la pila de 9 V, sin ESP32 ni DRV8833.**

1. Conecten la pila al arnés (en lugar de la LiPo), con SW-104S apagado.
2. Encendido:

   | Medir | Debe dar |
   |---|---|
   | Pad J1 contra J2 | ≈ 8.6–8.8 V (9 V menos D1) |
   | Salida de U2 | **5.0 V** |
   | J5.5V (después de D2) | ≈ 4.8–5.0 V |
   | VCC del header del DRV8833 (11,15) | **6.0 V** |
   | Pin VP del header del ESP32 | ≈ 2.1–2.2 V (8.7 V × 33/133) |

3. Polaridad: apaguen, inviertan la pila, prendan → J1 debe marcar ~0 V. **D1 funciona.**
4. Toquen U2, U3 y D2 después de 1 min: deben estar fríos (no hay carga).

> Si algo marca distinto: apaguen, revisen el punto con la hoja 1 y no sigan.

---

## Etapa 6 · ESP32 y firmware (sin DRV8833, sin motores)

1. Carguen el firmware **solo con USB** (sin pila) siguiendo [`firmware/robot-casero/README.md`](../../firmware/robot-casero/README.md). Abran el monitor a 115200 y escriban `estado`.
2. **Con el DevKit desconectado**, inserten el ESP32 en sus headers (USB-C hacia arriba) y vuelvan a conectar el USB. Deben ver:
   - "Robot casero V3 ...";
   - el LED azul parpadea (ESPERA);
   - un pitido al arrancar, si ya hay zumbador en J7.
3. Prueben los botones y la consola:

   | Acción | Resultado esperado |
   |---|---|
   | `estado` | `solo USB` |
   | START | Dos pitidos graves (rechazo: no hay calibración) |
   | CAL | Pasa a CALIBRACION: tic cada segundo. A los 15 s pitido descendente (sin sensores no hay contraste) y vuelve a ESPERA |
   | Medir J5.3V3 | 3.3 V |

4. Conecten la pila de 9 V **además** del USB:
   - `bat` debe dar ≈ 9 V.
   - Midan con el multímetro el voltaje de la pila y el de J1. La diferencia es la caída real de D1: `set caida_d1 <valor>` y luego `save`.

---

## Etapa 7 · DRV8833 y motores (RUEDAS EN EL AIRE)

1. Desconecten todo. Inserten el DRV8833 en su header (IN1…IN4 hacia el ESP32). El puente J1 del módulo **sin soldar**.
2. **Decisión de JP1 (nFAULT):**
   1. Con la pila conectada y el SW-104S encendido, midan el voltaje del pin ULT del header del DRV8833 (5,13) contra GND.
   2. **0 a 3.3 V** → cierren JP1 con una gota de soldadura, y en la consola `set usar_nfault 1` y `save`.
   3. **≈ 6 V** (el módulo tiene pull-up a VM) → **dejen JP1 abierto** y `usar_nfault` en 0.
3. Sin motores: `m 0.3 0` y midan en J4 (OUT1–OUT2) con el multímetro en DC → ≈ +1.6 V durante 1 s (promedio del PWM: 0.3 × 0.9 × 6 V). Con `m -0.3 0` debe dar el signo contrario. Luego `m 0 0.3` en J3.
4. Suelden los motores:
   - izquierdo a J4 (y = 16, 17);
   - derecho a J3 (y = 14, 15).
5. Con las ruedas en el aire:
   - `m 0.3 0` → la rueda **izquierda** gira **hacia adelante**. Si gira al revés: `set inv_izq 1`.
   - `m 0 0.3` → la rueda **derecha** hacia adelante. Si no: cambien `inv_der` (por defecto vale 1, porque el motor derecho va espejado).
   - Luego `save`.
6. Toquen el DRV8833 tras unas pruebas `m 0.8 0.8 3000`: tibio está bien; quemando, no.

---

## Etapa 8 · Sensores y primera vez con la LiPo

1. **Sensores:** conecten la QTR-8A (VCC a **3V3**, 3.3V BYPASS puenteado) o la barra casera a J5/J6. **A1 es el sensor de la IZQUIERDA del robot.**
2. Con USB y la consola, comprueben:

   | Comando | Qué buscar |
   |---|---|
   | `crudo` sobre blanco y sobre negro | Las columnas `on` deben cambiar mucho (blanco bajo, negro alto) y `off` casi igual en ambos |
   | `perf` | La lectura de sensores debe tardar < 1500 µs |

3. **Calibración:** oprimen CAL y pasan la barra sobre la línea (izquierda-derecha) 2–3 veces. Al ver contraste en todos los sensores, termina sola en ~1 s con 3 notas que **suben**.
4. Pongan la línea bajo el sensor de la izquierda y escriban `sens`: `pos` debe ser **negativo**. Si sale positivo, el cable de sensores está al revés.
5. **LiPo, primera vez:**
   1. Fusible puesto y SW-104S apagado. Revisen que el conector de la LiPo coincide en polaridad con el arnés.
   2. Conecten, enciendan y escriban `bat`: debe dar 7.4–8.4 V.
   3. LED parpadeando, nada caliente.
   4. Apaguen.

---

## Etapa 9 · Primera vuelta en la pista

1. Pesen el robot completo: **< 500 g**. Midan que quepa en **200 × 100 mm**.
2. Calibren con **CAL** dentro de los 15 s del reglamento. Pongan el robot en la línea y oprimen **START**:

   | Estado | Indicador |
   |---|---|
   | LISTO | LED fijo, doble pitido |
   | Segundo START | Arranca |

3. Primera vuelta lenta: `set vbase 0.25`. Para detenerlo, oprimen START.
4. **Si oscila (zigzag):** bajen `kp` de a 0.002 o suban `kd` de a 0.0002.
5. **Si se sale en curvas:** suban `kp` o bajen `vbase`.
6. Cuando quede bien: `save`. Las ganancias por defecto (kp 0.010, kd 0.0004) salen de la simulación [S], no de la pista.

| Indicación | Significa |
|---|---|
| LED fijo + 2 pitidos | LISTO |
| LED = línea, sin sonido | SIGUIENDO |
| LED rápido + pitidos seguidos | RECUPERACION: buscando la línea |
| Pitido largo, LED a 4 Hz | PARADA |
| 1 destello del LED + pausa, tono grave | ERROR 1: batería crítica (< 6.4 V) |
| 2 destellos + pausa | ERROR 2: falla del DRV8833 (solo con JP1 cerrado) |
| 3 pitidos graves cada 5 s | Batería baja (< 6.8 V): carguen |

## Si algo falla

| Síntoma | Revisar |
|---|---|
| El ESP32 no arranca con la pila (sí con USB) | D2 al revés; U2 no da 5 V; pin VIN equivocado (P07) |
| Los motores no se mueven con `m` | Que esté la pila (`bat`), EEP (D16) soldado, que el DRV8833 esté volteado como en la hoja 1, 6 V en VCC |
| Un motor solo gira hacia un lado | Una de las pistas IN1…IN4 está cortada (continuidad del header del ESP32 al del DRV8833) |
| `crudo` no cambia entre blanco y negro | Q1 con E y C invertidas (TCRT5000); LEDON sin conectar (QTR); altura de los sensores > 5 mm |
| ERROR 1 al arrancar con la LiPo cargada | `caida_d1` mal puesto o divisor con otros valores; `bat` debe coincidir con el multímetro |
| Reinicios al acelerar | Caída de la LiPo o falso contacto en GND; bajar `rampa` para acelerar más suave (`set rampa 3`) |

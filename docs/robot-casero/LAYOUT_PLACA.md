> **HISTÓRICO (11 nov 2026).** Este archivo describe el *plan B*: una sola placa fenólica de una cara, con 8 sensores directos y zumbador.
> Quedó sustituido por las decisiones **D18** (PCB de doble cara), **D19** (sin zumbador) y **D20** (placa de sensores con multiplexor).
> Las PCB vigentes están en `electronica/kicad/` (principal y sensores); la fabricación, en `electronica/kicad/FABRICACION_CASERA.md`.
> Ojo: el firmware (`firmware/robot-casero/`) todavía usa los pines de este archivo hasta que se resuelva **P18**.

# Robot casero · B. Layout de la placa fenólica

**Plantilla para imprimir (3 hojas tamaño carta):** [`placa/PLANTILLA_PLACA_1a1.pdf`](placa/PLANTILLA_PLACA_1a1.pdf)

| Hoja | Escala | Contenido | Para qué |
|---|---|---|---|
| 1 | **2:1** | Lado de componentes: dónde va cada pieza y cada pin | Leer y armar. **No sirve para taladrar.** |
| 2 | **1:1** | Lado COBRE ya en espejo, con una cruz en el centro de cada agujero | Dibujar con plumón y taladrar |
| 3 | **1:1** | La misma pista, invertida | Transferencia de tóner (impresora láser) |

**Antes de cortar o taladrar:**

1. Impriman la hoja 2 **al 100 %** (sin "ajustar a página").
2. Verifiquen con regla que la barra mide **50 mm**.
3. Pongan el ESP32 y el DRV8833 encima: sus pines deben caer en las cruces.

Si el DRV8833 no cae (sus filas podrían no estar a 15.24 mm, medida M32 [P]; el tamaño del módulo, 16 × 18.5 mm, ya está resuelto en M09), **avisen antes de taladrar**.

El layout sale de `herramientas/placa_principal.py`. Al ejecutarlo comprueba solo que:

- cada red queda unida;
- ninguna pista pasa por un pad o una pista de otra red;
- ningún componente alto choca con otro.

Resultado actual: **107 agujeros, 44 pistas, 0 puentes, sin errores.** Hay un solo aviso: el GND de J5/Q1 se une al resto a través del propio DevKit, que conecta internamente sus dos pines GND.

## 1. Cómo cortar la FEN20X20 (200 × 200 mm)

```
┌───────────────────────── 200 mm ─────────────────────────┐
│ ┌──────────────┐ ┌──────────────┐                        │
│ │ PRINCIPAL    │ │ PRINCIPAL    │   ← la 2.ª es repuesto: │
│ │ 91 × 86 mm   │ │ (repuesto)   │     si el cloruro se    │
│ └──────────────┘ └──────────────┘     come una pista, se  │
│ ┌────────────────────────────┐        repite sin comprar  │
│ │ BARRA SENSORES 100 × 25 mm │  (solo opción B:           │
│ └────────────────────────────┘   TCRT5000 sueltos)        │
│                 (resto: pruebas de soldadura)              │
└────────────────────────────────────────────────────────────┘
```

- Corten con segueta o rayando con cúter muchas veces por ambos lados y quebrando sobre la orilla de la mesa.
- Lijen las orillas.
- Antes de dibujar, limpien el cobre con fibra y alcohol hasta que brille.

## 2. Placa principal: dónde va cada pieza

Coordenadas en agujeros (x, y), contando desde el agujero de arriba a la izquierda. Vista desde el **lado de componentes** (hoja 1).

### Módulos

| Ref. | Pieza | Agujeros | Cómo se monta |
|---|---|---|---|
| U1 | ESP32 DevKit 30 pines, USB-C arriba | x = 14 y x = 24, de y = 4 a 18 | **2 tiras de header hembra 1×15.** El DevKit no se suelda. |
| U4 | Módulo DRV8833, **girado 180°** | x = 5 (salidas) y x = 11 (entradas), de y = 13 a 18 | 2 tiras de header hembra 1×6. Las letras IN1…IN4 quedan del lado del ESP32. J1 del módulo **sin soldar**. |
| U2 | MP1584 #1 (5.0 V) | IN+ (1,0), IN− (1,6), OUT+ (9,0), OUT− (9,6) | Pegado con cinta doble cara. Cada terminal se une a su pad con un trozo de alambre (pata de resistencia). |
| U3 | MP1584 #2 (6.0 V) | IN+ (1,24), IN− (1,30), OUT+ (9,24), OUT− (9,30) | Igual que U2. |

### Diodo, capacitores y resistencias

| Ref. | Pieza | Agujeros | Cómo se monta |
|---|---|---|---|
| D2 | 1N5822 | A (11,0), K (17,0) | Acostado. **Franja hacia la derecha.** Agujeros de 1.3–1.5 mm. |
| C1 | 470 µF 16 V | + (0,10), − (2,10) | Parado; patas abiertas a 5 mm. **Franja (−) a la derecha.** |
| C2 | 100 nF | (0,12) – (2,12) | Disco. |
| C4 | 470 µF 16 V | + (8,22), − (10,22) | Franja (−) a la derecha. |
| C5 | 100 nF | (8,20) – (10,20) | Disco; inclínenlo un poco hacia arriba. |
| C6 | 100 nF | (26,17) – (26,18) | Disco junto al pin VP. |
| R1 | 100 kΩ | (0,31) – (4,31) | Acostada. |
| R2 | 33 kΩ | (11,31) – (11,30) | Parada. |
| R4 | 1 kΩ | (29,6) – (30,6) | Parada. |
| R5 | 1 kΩ | (16,21) – (16,25) | Acostada. Queda bajo la orilla del ESP32; es baja y no estorba. |

### Transistores, botones, conectores y puente

| Ref. | Pieza | Agujeros | Cómo se monta |
|---|---|---|---|
| Q1 | 2N2222 | E (31,5), B (31,6), C (31,7) | Gírenlo hasta que su E caiga en el pad E (P05). |
| Q2 | 2N2222 | C (18,24), B (18,25), E (18,26) | Igual que Q1. |
| SW2 | START, 6×6 | señal (15,24), GND (13,26); las otras 2 patas solo sujetan | Solo trabajan las patas en **diagonal**. |
| SW3 | CAL, 6×6 | señal (23,24), GND (25,26) | Igual que SW2. |
| J1 / J2 | Cables de batería BAT+ / BAT− | (0,7) / (2,7) | 18 AWG estañado. Pad grande de 3 mm. |
| J3 / J4 | Motor DER (OUT3, OUT4) / IZQ (OUT1, OUT2) | x = 3, y = 14–15 / y = 16–17 | Cable del motor soldado directo, o header macho. |
| J5 | Sensores: 3V3, 5V, GND, LED_ON, EMIT− | x = 28, y = 3 a 7 | Header macho 1×5. |
| J6 | Sensores A1…A8 | x = 28, y = 9 a 16 | Header macho 1×8. |
| J7 | Zumbador (+ arriba, − abajo) | (21,23) – (21,24) | Header macho 1×2. |
| JP1 | Puente de soldadura nFAULT | (5,10) – (5,11) | **Abierto.** Se decide en la etapa 7 (paso 2) del manual; ver P13. |

### Pistas

Las pistas son de 1 mm (señales) y de 1.5 mm (VBAT, GND, VM, 5 V y motores).

- **Rieles:** VBAT corre por toda la orilla izquierda (x = 0) y GND por x = 2, con el bus de abajo en y = 30.
- **Señales del ESP32:**
  - Control del DRV8833 en rectas: y = 13, 14, 17 y 18.
  - Sensores en rectas de x = 24 a x = 28.
  - START, zumbador y CAL bajan **por debajo del DevKit**, por el lado del cobre (columnas 15, 16 y 23).
- **Batería al ADC:** VBAT_ADC da la vuelta por la orilla de abajo (y = 31) y sube por x = 32 hasta VP.

El dibujo exacto está en la hoja 2.

## 3. Pasar el dibujo al cobre

**A · Plumón permanente** (no requiere láser). Funciona si la línea queda opaca: dos pasadas.

1. Peguen la hoja 2 sobre el cobre con cinta.
2. Marquen cada cruz con un punzón o un clavo.
3. Quiten la hoja y **taladren primero** con la broca de 0.8 mm. Así los agujeros guían el dibujo.
4. Dibujen las pistas uniendo los agujeros como en la hoja 2, que está en espejo y por eso se copia tal cual.
5. Hagan pads redondos de ~2 mm en cada agujero.

**B · Transferencia de tóner** (impresora láser y papel couché):

1. Impriman la hoja 3.
2. Planchen 3–5 min con la tinta contra el cobre.
3. Remojen y retiren el papel.
4. Retoquen con plumón.

**Ataque y acabado:**

1. Cloruro férrico tibio, moviendo el recipiente, 15–30 min hasta que no quede cobre entre pistas.
2. Enjuaguen y quiten la tinta con thinner o alcohol.
3. Revisen con lupa contra la hoja 2.
4. Prueben la continuidad de las pistas largas (VBAT, GND, VBAT_ADC) **y que no haya continuidad entre VBAT y GND**.

**Taladrado:**

| Broca | Agujeros |
|---|---|
| 0.8 mm | Todo lo demás (105 agujeros) |
| 1.3–1.5 mm | Las 2 patas de D2 (Ø1.30 mm [V ST]) |

Los pines de header de 0.64 mm cuadrados tienen 0.9 mm de diagonal: si no entran, agranden el agujero girando la broca a mano.

**Si la FEN20X20 resulta ser perforada** (con agujeros cada 2.54 mm): mismas posiciones. Cada pista se hace con alambre estañado (patas de resistencia) siguiendo el dibujo de la hoja 2, soldado agujero por agujero.

## 4. Barra de sensores (solo la opción B: 8 TCRT5000 sueltos)

Con la QTR-8A **no** se fabrica barra: la QTR se atornilla al frente y se cablea a J5/J6 con cable delgado.

**Barra casera de 100 × 25 mm.** Va con el cobre hacia ARRIBA y todas las piezas por abajo, como en cualquier placa de una cara:

- **Sensores:** quedan colgando hacia el piso. Miden 7 mm y su cara debe quedar a ~2.5 mm del piso [V Vishay]. Las patas pasan a la cara de cobre y se sueldan arriba.
- **Resistencias:** van acostadas también por abajo, entre sensor y sensor. Miden 2.5 mm de alto, menos que los 7 mm del sensor, así que no tocan el piso.
- **Separación:** 8 sensores cada **4 agujeros (10.16 mm)**, centrados. Ocupan 71 mm de ancho y la línea de 25 mm siempre cubre 2 o 3. En `config.h` se pone `PASO_SENSORES_MM 10.16f`.

**Pistas: 4 rieles a lo largo de la barra**, de arriba abajo:

| Riel | Lo que se conecta |
|---|---|
| 5 V | Una 330 Ω por sensor, al ánodo A |
| EMIT− | Los cátodos K |
| 3V3 | Una 10 kΩ por sensor, al colector C |
| GND | Los emisores E |

Cada colector C sale además a su pin del header 1×8 (A1 a la izquierda del robot). Los rieles llegan a un header 1×5 con el mismo orden de J5. Cablen las dos tiras a J5/J6 con cable delgado (dupont).

**Pendiente (M19):** el orden físico de las 4 patas del TCRT5000. Antes de dibujar la barra, pongan un sensor sobre papel y marquen dónde caen las patas. Con eso se dibuja la barra; no se taladra nada antes.

## 5. Tabla de conexiones (red → pines)

Generada por el script (`placa/redes.json`).

| Red | Pines |
|---|---|
| VBAT | J1.+, C1.+, C2, R1, U2.IN+, U3.IN+ |
| GND | J2.−, U1.GND (×2), U4.GND, U2.IN−/OUT−, U3.IN−/OUT−, C1.−, C2, C4.−, C5, C6, R2, Q1.E, Q2.E, SW2, SW3, J5.GND |
| 5V | U2.OUT+, D2.A |
| VIN_ESP | D2.K, U1.VIN, J5.5V, J7.+ |
| VM | U3.OUT+, U4.VCC, C4.+, C5 |
| 3V3 | U1.3V3, J5.3V3 |
| AIN1 / AIN2 / BIN1 / BIN2 | U1.D19 / D21 / D22 / D23 → U4.IN1 / IN2 / IN3 / IN4 |
| NSLEEP | U1.D16, U4.EEP |
| NFAULT → NFAULT_ESP | U4.ULT → JP1 → U1.D15 |
| MI_A, MI_B / MD_A, MD_B | U4.OUT1, OUT2 → J4 / U4.OUT3, OUT4 → J3 |
| START / CAL | U1.D18 → SW2 / U1.D14 → SW3 |
| ZUMB → Q2B / ZUMB_K | U1.D4 → R5 → Q2.B / Q2.C → J7.− |
| EMIS → Q1B / EMIT_K | U1.D13 → R4 → Q1.B; U1.D13 → J5.LED_ON / Q1.C → J5.EMIT− |
| A1…A8 | U1.D27, D26, D25, D33, D32, D35, D34, VN → J6.A1…A8 |
| VBAT_ADC | R1, R2, C6 → U1.VP |

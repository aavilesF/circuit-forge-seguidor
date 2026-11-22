> **HISTÓRICO (rama anterior `engineering/robot-casero`). No es información vigente de V2.** Inventario, decisiones y pendientes vigentes: `v2/inventario.csv`, `v2/docs/decisiones.md`, `docs/pendientes-por-confirmar.md`. Estado de cada documento: `v2/docs/ESTADO-DOCUMENTOS.md`.

# Cómo funciona el multiplexor 74HC4067 (explicación sencilla)

**Sí, es la pieza correcta.** Un *multiplexor analógico* (a veces llamado "traductor" para ahorrar pines) es un **selector**: tiene 16 entradas (los 16 sensores)
y una sola salida. Con 4 pines de control le dices "conecta la entrada número N a la salida". Así leemos 12 sensores usando **un solo pin analógico** del ESP32
(más 4 pines de selección) en lugar de 12 pines analógicos.

## Pines del módulo "en barrita" (nombres típicos; el orden físico se confirma con la pieza)

| Pin | Qué hace | Se conecta a |
|---|---|---|
| VCC | Alimentación | **3.3 V** (no 5 V, ver cuidados) |
| GND | Tierra | GND |
| S0, S1, S2, S3 | **Selección**: número binario (0 a 15) del canal activo | 4 pines digitales del ESP32 (GPIO25, 26, 27, 33) |
| SIG (también COM) | **Señal común de salida**: aquí aparece el canal elegido | Un pin ADC1 del ESP32 (GPIO34) |
| EN (o /E, "enable" = habilitar) | Apagado/encendido del chip. **Activo en bajo**: con 0 V el chip funciona | **GND** (siempre habilitado) |
| C0 … C15 (o CH0…CH15) | Las 16 entradas | Un sensor en cada una (usamos C0 a C11) |

## Cómo se elige el canal
S0 es el bit 1, S1 el bit 2, S2 el bit 4 y S3 el bit 8. Ejemplos: S3 S2 S1 S0 = 0000 → canal 0; 0101 → canal 5; 1011 → canal 11.
El firmware hace esto 12 veces por lectura: pone los 4 bits, **espera ~10 µs** a que la señal se estabilice (el chip tiene resistencia interna de
unos cientos de ohm), lee el ADC y pasa al siguiente canal.

## Cuidados con ADC1 y ADC2 del ESP32
- El ESP32 tiene dos convertidores analógicos. **ADC2 (GPIO0, 2, 4, 12–15, 25–27) se bloquea cuando el WiFi o Bluetooth están encendidos.** El reglamento
  prohíbe comunicación inalámbrica en competencia, así que no se enciende, pero **aun así usamos ADC1** (GPIO32 a 39) para no depender de eso.
- Usamos **GPIO34** (ADC1, canal 6) para SIG. Los GPIO34 a 39 son *solo entrada*: perfecto para leer.
- **Nunca más de 3.3 V en SIG.** Por eso el multiplexor y los sensores se alimentan a 3.3 V: la salida jamás pasa de ese valor. Si se alimentara a 5 V,
  una lectura alta podría dañar el ESP32.
- El ADC del ESP32 no es lineal en los extremos (cerca de 0 V y de 3.3 V). Se compensa con la calibración de blanco y negro (los 15 s del reglamento).
- Los pines S0 a S3 están en GPIO25, 26, 27 y 33. Los GPIO25, 26 y 27 son ADC2, pero aquí se usan como salidas digitales, así que no hay problema.
- 100 nF entre VCC y GND cerca del módulo evita lecturas ruidosas.

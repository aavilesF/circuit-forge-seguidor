<!-- Generado por herramientas/generar_diagramas.py desde firmware/seguidor/pines.h. No editar a mano. -->

| Señal (pines.h) | GPIO | Conexión | Nota |
|---|---|---|---|
| `PIN_LED` | 2 | LED de estado | Salida (pin de arranque: no forzar al encender) |
| `PIN_START` | 4 | Botón START a GND | Pull-up interno |
| `PIN_EMISORES` | 13 | Compuerta del MOSFET de los LED IR (con resistencia a GND) | Salida |
| `PIN_CAL` | 14 | Botón CAL a GND | Pull-up interno |
| `PIN_STBY` | 16 | TB6612 STBY | Salida (bajo = motores libres) |
| `PIN_PWMB` | 17 | TB6612 PWMB (rueda derecha) | PWM 20 kHz |
| `PIN_PWMA` | 18 | TB6612 PWMA (rueda izquierda) | PWM 20 kHz |
| `PIN_AIN1` | 19 | TB6612 AIN1 | Salida |
| `PIN_AIN2` | 21 | TB6612 AIN2 | Salida |
| `PIN_BIN1` | 22 | TB6612 BIN1 | Salida |
| `PIN_BIN2` | 23 | TB6612 BIN2 | Salida |
| `PIN_MUX_S0` | 25 | Dirección S0 de los multiplexores | Salida |
| `PIN_MUX_S1` | 26 | Dirección S1 | Salida |
| `PIN_MUX_S2` | 27 | Dirección S2 | Salida |
| `PIN_MUX_S3` | 33 | Dirección S3 | Salida |
| `PIN_MUX_SIG1` | 34 | SIG del multiplexor 1 (canales 0-15) | Solo entrada, ADC1 |
| `PIN_MUX_SIG2` | 35 | SIG del multiplexor 2 (canales 16-23); sin conectar con 8 sensores | Solo entrada, ADC1 |
| `PIN_BATERIA` | 36 | Divisor de batería 100k/47k (punto medio) | Solo entrada, ADC1 |
| `PIN_PERFIL` | 39 | Perilla de perfil de velocidad (centro del potenciómetro, extremos a 3V3 y GND) | Solo entrada, ADC1 |

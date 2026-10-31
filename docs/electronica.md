# Electrónica

Diagramas: `docs/diagramas/01_bloques.png` (energía y señales) y `02_cableado.png` (tabla de pines).
La tabla de pines se genera de `firmware/seguidor/pines.h` (`docs/diagramas/pines.md`); **si cambias un pin, cámbialo solo en `pines.h` y corre `python3 herramientas/generar_diagramas.py`.**
El script se detiene si hay un GPIO repetido, si usas pines de la flash (6-11) o uno solo-entrada como salida.

## Reglas

1. Todo lo que toque un pin del ESP32 trabaja a **3.3 V** (sensores, TB6612 VCC, multiplexores, botones).
2. Motores a ~6 V desde su propio regulador; el ESP32 a 5 V por VIN desde otro regulador. Nunca alimentar motores del regulador del ESP32.
   **Checkpoint C2 abierto** (`ARQUITECTURA.md` §3.6): la ficha del MP1584 no avala 6 V desde una 2S; se recomienda motores directo de la batería con compensación en firmware (`MOTOR_DESDE_BATERIA`).
3. Una sola unión de tierras (estrella) cerca de la batería. Los cables de los motores lejos de los de los sensores.
4. Capacitor de 100-470 µF cerca de VM del TB6612 y 100 nF en cada módulo.
5. Fusible reseteable en serie con el positivo de la batería.
6. Emisores IR: el **QTR-8A de Pololu** ya trae MOSFET; su pin LEDON (pull-up interno, bajo = apagado) va **directo** al GPIO13. Solo con sensores sueltos hace falta un MOSFET de nivel lógico (compuerta al GPIO13 con 100 Ω en serie y 100 kΩ a GND). Al clon de UNIT hay que revisarle si tiene ese pin (protocolo F5).
7. No usar WiFi ni Bluetooth: el reglamento los prohíbe en competencia. El firmware no los incluye.

## Pines del ESP32 que importan

- GPIO 34, 35, 36, 39: solo entrada (los usamos para los sensores, la batería y la perilla).
- GPIO 6-11: conectados a la memoria flash, nunca usar.
- GPIO 0, 2, 5, 12, 15: condicionan el arranque. Solo usamos el 2 (LED): no conectar nada que lo fuerce a nivel alto o bajo al encender.
- GPIO 16 y 17 libres en la placa **ESP32-WROOM-32 (esp32dev)**; en módulos WROVER (con PSRAM) están ocupados. Revisar la etiqueta del módulo al comprar.
- Solo ADC1 (GPIO 32-39): el ADC2 no es confiable y lo evitamos. Por eso 8 sensores necesitan multiplexor.

## Lectura de sensores

- Multiplexor CD74HC4067: 16 canales por chip. Con 8 sensores se usa un chip (SIG1); con 24, dos chips que comparten S0-S3 (SIG1 y SIG2) y se leen a la vez.
- Para cada canal: se enciende el emisor, se espera, se lee; luego se apaga y se lee otra vez; la diferencia quita la luz ambiente (reglamento: debe funcionar con cualquier iluminación).
- **VERIFICAR al recibir el sensor:** (a) si el voltaje sube o baja sobre la línea negra (`ALTO_ES_NEGRO` en `pines.h`), (b) el paso entre sensores, (c) que se alimenta y da señal a 3.3 V, (d) si tiene pin para apagar emisores.
- Espera del multiplexor: 15 µs (≈ 6 τ con las salidas de 47 kΩ del QTR-8A y ~50 pF del mux); emisores: 30 µs. Ajustables en `pines.h`; medir con `diag`.
- El ADC a 11 dB mide bien de 150 a 2450 mV (Espressif). El sensor a 3.3 V puede pasar de eso sobre negro: se satura en 4095, lo cual no estorba (la calibración solo necesita distinguir blanco de negro).

## Batería

Divisor 100 kΩ (arriba) / **33 kΩ** (abajo): 8.4 V → 2.08 V en el pin, dentro del rango recomendado del ADC (antes 47 kΩ daba 2.69 V, fuera de rango: H03). El firmware no arranca con menos de 6.8 V y detiene el robot si el voltaje filtrado queda bajo 6.4 V durante 300 ms.
Cargar siempre con cargador balanceado y bolsa/caja para LiPo.

## Lista de comprobación de cada conexión

Ver `docs/PROTOCOLO_PRUEBAS.md` (cada etapa tiene qué medir y qué valor esperar).

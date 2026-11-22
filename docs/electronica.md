> **HISTÓRICO (rama anterior `engineering/robot-casero`). No es información vigente de V2.** Inventario, decisiones y pendientes vigentes: `v2/inventario.csv`, `v2/docs/decisiones.md`, `docs/pendientes-por-confirmar.md`. Estado de cada documento: `v2/docs/ESTADO-DOCUMENTOS.md`.

# Electrónica

Diagramas: `docs/diagramas/01_bloques.png` (energía y señales) y `02_cableado.png` (tabla de pines).
La tabla de pines se genera de `firmware/seguidor/pines.h` (`docs/diagramas/pines.md`); **si cambias un pin, cámbialo solo en `pines.h` y corre `python3 herramientas/generar_diagramas.py`.**
El script se detiene si hay un GPIO repetido, si usas pines de la flash (6-11) o uno solo-entrada como salida.

## Reglas

1. Todo lo que toque un pin del ESP32 trabaja a **3.3 V** (sensores, TB6612 VCC, multiplexores, botones).
2. Motores a ~6 V desde su propio regulador; el ESP32 a 5 V por VIN desde otro regulador. Nunca alimentar motores del regulador del ESP32.
3. Una sola unión de tierras (estrella) cerca de la batería. Los cables de los motores lejos de los de los sensores.
4. Capacitor de 100-470 µF cerca de VM del TB6612 y 100 nF en cada módulo.
5. Fusible reseteable en serie con el positivo de la batería.
6. Los LED infrarrojos se encienden con un **MOSFET de nivel lógico** (compuerta al GPIO13 con 100 Ω en serie y 100 kΩ a GND para que quede apagado al arrancar). Las resistencias de los LED se calculan con la ficha del sensor.
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
- El tiempo de espera del multiplexor (4 µs) y de los emisores (30 µs) son supuestos; si hay lecturas "arrastradas" entre canales, aumentarlos.

## Batería

Divisor 100 kΩ (arriba) / 47 kΩ (abajo): 8.4 V → 2.7 V en el pin (seguro, máximo 3.3 V). El firmware no arranca con menos de 6.6 V (3.3 V por celda) y detiene el robot si baja de 6.2 V.
Cargar siempre con cargador balanceado y bolsa/caja para LiPo.

## Lista de comprobación de cada conexión

Ver `docs/armado.md` (cada etapa tiene qué medir y qué valor esperar).

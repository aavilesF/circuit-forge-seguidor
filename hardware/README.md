# Hardware — arquitectura de $2,000 MXN

## Electrónica (`electronics/`)

La arquitectura vigente **no usa PCB propia**: es un conjunto de módulos (ESP32 DevKit, TB6612FNG, MP1584, 74HC4067, barra clon QTR-8A) conectados en una placa perforada de 5 × 7 cm.

- `conexiones.csv`: lista de redes (de dónde a dónde, dominio de voltaje, corriente máxima y notas). Es la referencia para cablear.
- `verificar_electrica.py`: hace las veces de ERC mientras no haya esquemático en KiCad. Comprueba:
  - que los pines del CSV coincidan con `firmware/sf/pines_sf.h`;
  - las reglas del ESP32-WROOM-32 (pines de flash, ADC1, pines solo de entrada, pines de arranque);
  - los límites del driver (VM, bloqueo, frenado inverso), el fusible y el regulador;
  - el dominio de voltaje de la barra.
  Se ejecuta dentro de `pruebas/ejecutar_todo.sh`.

**No hay Gerbers.** No se generaron porque no hay PCB en esta arquitectura y no hay un esquemático verificado con ERC/DRC. KiCad 7 se puede instalar en el entorno de trabajo (`apt-get install kicad`), pero el esquemático no se ha dibujado: está pendiente (ver `docs/ESTADO_PROYECTO.md`).

**Avisos abiertos:**
1. La barra clon alimentada a 5 V puede entregar más de 3.3 V al mux. Hay que poner 10 kΩ en serie por canal (BOM R1) o alimentar la barra a 3.3 V. Medir antes de conectar.
2. El clon no documenta el pin de los emisores. El firmware trabaja sin resta de luz ambiente (`barras.recta8_tcrt.resta_ambiente: false`). **Nunca** manejar los LED directo desde un GPIO.

## Mecánica (`mechanical/`)

- `disposicion.py` dibuja la planta (`disposicion_planta.png/.svg`) a partir de las posiciones, medidas y masas del YAML. Comprueba la caja del reglamento (con 4 mm de holgura por lado), los choques entre piezas del mismo nivel, el CG entre el eje y el apoyo, y la masa.
- **No es el CAD definitivo.** Las medidas son estimadas o vienen de anuncios: motor con encoder, apoyo, batería, módulos. El generador paramétrico anterior (`legado/speed_follower_v1/cad/`) se tomará como base para el STL cuando se midan las piezas.
- Resultado actual: 141 × 92 mm, 132 g, CG a 22.4 mm delante del eje; 0 fallas.

> **HISTÓRICO (rama anterior `engineering/robot-casero`). No es información vigente de V2.** Inventario, decisiones y pendientes vigentes: `v2/inventario.csv`, `v2/docs/decisiones.md`, `docs/pendientes-por-confirmar.md`. Estado de cada documento: `v2/docs/ESTADO-DOCUMENTOS.md`.

# Guía de armado y pruebas

Orden pensado para detectar errores **antes** de que quemen algo. Cada etapa tiene un criterio de aprobado. No pasar a la siguiente si falla.
Herramientas mínimas: multímetro, cable USB de datos, soldador, vernier, báscula.

> Estado del firmware: la lógica (posición, PID, control) tiene 60 pruebas aprobadas y un simulador. El código de hardware del ESP32 se verificó **solo
> de sintaxis contra un stub** (`pruebas/verificar_sintaxis_esp32.sh`); **no se pudo compilar con el SDK real ni probar en la placa**. La etapa 1 es la primera compilación real:
> si aparece un error, es esperable y se corrige ahí.

## Etapa 0 - Al recibir las piezas
1. Pesar cada pieza y anotar. Medir con vernier: paso entre sensores, ancho de la placa de sensores, diámetro de rueda, largo del motor con caja reductora, alto del caster.
2. Revisar la etiqueta del ESP32: debe ser WROOM-32 (no WROVER) y de 38 pines; comparar la serigrafía con `pines.h`.
3. Actualizar en `pines.h` / `parametros.h` lo que difiera y correr `python3 herramientas/generar_diagramas.py` para ver si sigue cabiendo.

## Etapa 1 - ESP32 solo, por USB
1. Instalar Arduino IDE (paquete "esp32 by Espressif") o PlatformIO. Placa: **ESP32 Dev Module**.
2. Abrir `firmware/seguidor/seguidor.ino` y compilar. **Aprobado:** compila sin errores y sube.
3. Monitor serie a 115200: aparece "Circuit Forge - seguidor listo" y los parámetros. Escribir `ayuda`.
4. Probar el LED: parpadea lento en estado ESPERA.

## Etapa 2 - Alimentación (sin motores ni sensores conectados)
1. Batería -> fusible -> reguladores. Con multímetro, **antes de conectar el ESP32**: regulador de 5 V = 5.0 ± 0.2 V; regulador de motores = 6.0 ± 0.3 V.
2. Conectar el regulador de 5 V a VIN del ESP32. **Aprobado:** el pin 3V3 mide 3.3 V y el consumo en reposo es de decenas de mA.
3. Comando `bat`: debe coincidir con el multímetro en ±0.2 V. Si no, ajustar `DIVISOR_BAT` en `pines.h`.

## Etapa 3 - Botones y perilla
- Botón START (GPIO4) y CAL (GPIO14) a GND. Con el robot en ESPERA, CAL inicia calibración (LED rápido); START solo funciona si ya hay una calibración guardada.
- Perilla en GPIO39: extremos a 3V3 y GND.

## Etapa 4 - Motores (ruedas en el aire, sin tocar el piso)
1. Conectar TB6612 y motores. Alimentar VM del driver desde el regulador de 6 V, VCC a 3.3 V, STBY al GPIO16.
2. Comando `m 0.3 0.3`: ambas ruedas giran 1 s **hacia adelante**. Si una gira al revés: `INVERTIR_IZQ` / `INVERTIR_DER` en `pines.h` (o intercambiar los cables del motor).
3. `m 0.3 0.1`: la izquierda más rápida (el robot, en el piso, giraría a la derecha). Si la rueda "izquierda" es la derecha, cruzar los canales A y B.
4. **Aprobado:** adelante, giro y paro correctos; el driver no se calienta; el fusible no se dispara.

## Etapa 5 - Sensores (sobre la pista, robot en la mano)
1. Conectar multiplexores y sensores a 3.3 V. Pasar `crudo` sobre blanco y sobre negro: los valores deben cambiar en cientos de cuentas (si cambian poco, revisar alimentación, altura 8-10 mm y emisores).
2. Anotar si el valor sube o baja en el negro. Si **sube**, `ALTO_ES_NEGRO = true`; si baja, `false` (en `pines.h`).
3. Calibrar: botón CAL, mover el robot a mano de lado a lado sobre la línea durante ~5 s, CAL otra vez. **Aprobado:** vuelve a LISTO (LED fijo). Si imprime "calibracion insuficiente", algún sensor no vio blanco y negro.
4. Comando `sens`: con el robot centrado sobre la línea, `pos` ≈ 0 mm. Mover la línea a la derecha del robot: `pos` **positivo**. Con 8 sensores, cada sensor debe iluminarse en su turno al recorrer la barra: si el orden está invertido o desordenado, el cableado del multiplexor no corresponde (corregir en la conexión, no en el código).

## Etapa 6 - Primera marcha
1. Pista simple: una recta con una curva suave, de radio grande. Perilla al mínimo (25 %).
2. `tel 1` y START: revisar el periodo real: columna 1 en µs. **Aprobado:** menos de ~4000 µs. Si es mayor, ver `docs/simulacion.md` (retardo): reducir canales o quitar la lectura con emisores apagados.
3. Si oscila mucho: bajar `kp` (`set kp 0.02`). Si se sale en curvas: subir `kd` o bajar `vbase`. Si es lento y ancho: subir `kp`.

## Etapa 7 - Ajuste (orden recomendado)
1. `vbase` bajo (0.2-0.3) y `kp` hasta que siga sin zigzaguear (empezar en 0.02; el valor 0.04 sale de la simulación, no del robot real).
2. Subir `kd` hasta que desaparezca el zigzag en las rectas (0.0005 -> 0.002).
3. Subir `vbase` de 0.05 en 0.05 mientras no se salga en las curvas de 15 cm.
4. Guardar con `save` (queda en memoria del ESP32). Anotar los valores buenos en `docs/decisiones.md` o en `modificaciones/`.
5. Probar con huecos de 5 mm, línea perdida (debe buscar y luego detenerse) y con luz distinta.

## Antes de la competencia
- Pesar el robot completo (máximo 500 g) y medir la huella (20 × 10 cm).
- Desconectar el cable USB; no habilitar nada inalámbrico.
- Batería cargada (> 7.8 V). Confirmar el arranque con el botón.
- Recordar los 15 s para calibrar y colocar. El reglamento puede cambiar hasta el 18 de noviembre: releerlo.

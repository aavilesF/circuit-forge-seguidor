# Firmware (ESP32, Arduino)

`firmware/sf/` se abre con Arduino IDE (la carpeta y el `.ino` se llaman igual).

| Archivo | Contenido |
|---|---|
| `config_maestra.h` | **Generado** de `config/robot_maestro.yaml` por `herramientas/generar_config_firmware.py`. No editar a mano |
| `sf_logica.*` | Lógica pura en C++17: estimación de la línea (`estimar_coord`) y control C2/C3m/C3g. Verificada contra el simulador |
| `pines_sf.h` | Pines del ESP32; el robot y los parámetros salen de `config_maestra.h` |
| `hardware_sf.*` | ADC + mux, PWM (LEDC), driver TB6612FNG o DRV8833 (`conductor.modelo` del YAML) |
| `sf.ino` | Estados, calibración, memoria (NVS) y consola serie |

## Estado de la verificación

| Verificación | Resultado | Cómo |
|---|---|---|
| Lógica = simulador (C2, C3m, C3g, estimar_coord) | Probado en software | `pruebas/sf/ejecutar.sh` (g++ con ASan/UBSan) |
| Sintaxis de todo el firmware | Probado en software **contra un stub de Arduino** | `pruebas/sf/verificar_sintaxis_sf.sh` |
| **Compilación con el toolchain real del ESP32** | **PENDIENTE** | En el entorno de trabajo, el proxy bloquea las descargas de Espressif y Arduino (403). Se debe compilar en una laptop del equipo |

## Compilar (pendiente; hacerlo en la laptop del equipo)

1. Arduino IDE 2.x → Preferencias → URL adicionales del gestor de placas: la del índice oficial de Espressif para arduino-esp32 (ver la documentación de arduino-esp32).
2. Gestor de placas → instalar "esp32 by Espressif Systems" (3.x).
3. Placa: "ESP32 Dev Module". Abrir `firmware/sf/sf.ino` → Verificar.
4. Si falla, guardar el mensaje completo en `modificaciones/` y avisar. Las API más expuestas a errores son `ledcAttach` (3.x) / `ledcSetup` (2.x) y `analogReadMilliVolts`.

Alternativa por línea de comandos: `arduino-cli compile --fqbn esp32:esp32:esp32 firmware/sf`.

**Antes de subirlo al robot:** medir los motores (M7) y la barra (paso, ruido, polaridad), actualizar el YAML, regenerar la cabecera y repetir el ajuste final (`python3 sim/fase3.py G`).

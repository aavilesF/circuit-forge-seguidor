# Firmware — STM32G431CBT6 (PCB-chasis)

Firmware definitivo del Speed Follower para la PCB de `hardware/electronics/`. Registros CMSIS, sin HAL ni Arduino.
El firmware de ESP32 de la Fase 3 quedó en `legado/firmware_esp32_fase3/` (histórico).

## Estructura

| Ruta | Contenido |
|---|---|
| `config_maestra.h` | **Generado** de `config/robot_maestro.yaml`: motor, geometría, posición de los 16 sensores, parámetros del control (competencia y modo seguro), batería, inversión de motores y encoders |
| `logica/` | C++17 puro, sin dependencias del MCU, probado en la PC: `sf_logica` (estimación de línea y control C2/C3m/C3g/C3e, **igual al simulador**), `estados` (máquina de estados, botones, batería), `posicion` (reflectancia y calibración) |
| `stm32/src/pines_generados.h` | **Generado** de `hardware/electronics/generador/diseno.py`: pines, funciones alternas, canales ADC de cada sensor y canal de TIM1 de cada entrada del DRV8833 (los mismos del esquemático y la PCB) |
| `stm32/src/hw.*` | Capa de hardware: reloj 170 MHz (HSI16 + PLL), ADC1/ADC2 en paralelo, PWM 20 kHz (TIM1), encoders (TIM2/TIM3 en modo cuadratura), base de 1 kHz (TIM6), USART1 con colas, flash para parámetros |
| `stm32/src/main.cpp` | Ciclo de control, seguridad, calibración, consola serie y memoria |
| `stm32/Makefile`, `STM32G431CBTX_FLASH.ld` | Compilación con Arm GNU Toolchain |
| `stm32/vendor/` | CMSIS Core y CMSIS Device STM32G4 de ST (Apache-2.0, sin modificar; ver `vendor/ORIGEN.md`) |

## Funcionamiento

- **Ciclo de 1 kHz**: luz ambiente (emisores apagados) → emisores encendidos 200 µs → segunda lectura → reflectancia
  = ambiente − encendido → normalización con la calibración → posición de la línea (`sf::estimar_coord` con la posición
  real de cada sensor del arco) → encoders → control → PWM. Lectura completa ≈ 225 µs.
- **Puente H**: decaimiento lento (una entrada fija en alto, la otra con PWM), 20 kHz.
- **Control vigente (competencia)**: C3m, curvatura del perfil desde el modelo del motor, v_max 0.8165 m/s.
  **Modo seguro** (`modo seguro` en la consola): C3e con curvatura de los encoders, v_max 0.6327 m/s, 100 % de éxito en
  las 6 plantas de incertidumbre del simulador (`sim/resultados/final/E_eleccion.json`).
- **Seguridad**: los motores solo se habilitan con START (regla R08), calibración válida y batería ≥ 6.8 V. Se detiene:
  línea perdida > 0.3 s, batería < 6.4 V sostenida, nFAULT del DRV8833, rueda trabada 0.3 s (ciclo > 0.5 sin
  giro en el encoder), lecturas imposibles de los sensores, o START otra vez. `nSLEEP` del puente H queda en bajo cuando
  los motores no están habilitados.
- **Calibración** (regla C03): botón CAL → hasta 10 s deslizando el robot **a mano** sobre la línea (los motores no se
  mueven) → CAL otra vez. Si los 16 sensores vieron blanco y negro (≥ 150 cuentas de diferencia) se guarda en la flash.
- **LEDs**: OK (verde) fijo = listo/siguiendo, parpadeo = calibrando. ERR (rojo) fijo = estado ERROR (nFAULT, rueda
  trabada, sensores imposibles; se sale con CAL); parpadeo = calibración insuficiente, batería baja o parada por línea
  perdida o batería crítica. Tabla completa en `docs/MANUAL_ENSAMBLAJE.md` §10.
- **Consola** (115200 8N1 por el puerto serie virtual del STLINK-V3MINIE): `?` ayuda, `t` telemetría a 50 Hz, `r`
  lecturas crudas, `p` parámetros, `set <param> <valor>`, `modo comp|seguro`, `w` guardar, `defecto`,
  `prueba <izq> <der>` (2 s, ciclo ≤ 0.5, solo detenido y con las ruedas en el aire).

## Estado de la verificación

| Verificación | Resultado | Cómo |
|---|---|---|
| Lógica = simulador (C2, C3m, C3g, C3e, estimar_coord) | ≤ 4.2 × 10⁻⁶ | `pruebas/sf/ejecutar.sh` (g++ con ASan/UBSan) |
| **Compilación con el toolchain real** | **Compila sin avisos** (`-Wall -Wextra -Werror`): 16.2 KB de flash (12.6 %), 4.7 KB de RAM; registro en `stm32/registro_compilacion.txt` | `make` con arm-none-eabi-gcc 13.2.1 (Arm GNU Toolchain 13.2.rel1, paquete de Ubuntu 24.04) |
| Tabla de vectores e interrupciones | Reset, SysTick, TIM6 y USART1 resueltos a las rutinas del firmware; pila inicial 0x20005800 | `arm-none-eabi-nm` (dentro de `pruebas/ejecutar_todo.sh`) |
| Ejecución en el STM32 real | **Pendiente**: no hay placa fabricada | Manual de ensamblaje, pasos E5-E9 |

## Compilar

### Linux (como se verificó)

```bash
sudo apt-get install gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib make
cd firmware/stm32 && make          # build/speed_follower.elf, .hex y .bin
```

### Windows (procedimiento reproducible)

1. Instalar **Arm GNU Toolchain** para `arm-none-eabi` (versión 13.2.Rel1 o posterior) desde developer.arm.com
   (instalador `arm-gnu-toolchain-...-mingw-w64-...-arm-none-eabi.exe`). Marcar "Add path to environment variable".
2. Instalar **make**: con MSYS2 (`pacman -S make`, y agregar `C:\msys64\usr\bin` al PATH) o con
   "xPack Windows Build Tools".
3. Instalar **STM32CubeProgrammer** de st.com (incluye `STM32_Programmer_CLI.exe` y el controlador del STLINK).
4. En PowerShell:
   ```powershell
   arm-none-eabi-gcc --version          # debe responder 13.x o posterior
   cd firmware\stm32
   make                                 # genera build\speed_follower.hex
   STM32_Programmer_CLI -c port=SWD mode=UR -w build\speed_follower.hex -v -rst
   ```
   (o `make flash`). La placa debe estar alimentada por su batería: el STLINK-V3MINIE no la alimenta.
5. Consola: el STLINK-V3MINIE aparece como "STMicroelectronics STLink Virtual COM Port (COMx)"; abrirlo a 115200 8N1
   (PuTTY, el monitor serie de Arduino IDE o `python -m serial.tools.miniterm COMx 115200`).

### Después de cambiar el YAML o el diseño de la PCB

```bash
python3 herramientas/generar_config_firmware.py   # regenera config_maestra.h y pines_generados.h
pruebas/ejecutar_todo.sh                          # incluye la compilación real si arm-none-eabi-gcc está instalado
```
`generar_config_firmware.py` lee los símbolos de KiCad 9 (variable `KICAD_SHARE`, p. ej.
`C:\Program Files\KiCad\9.0\share\kicad`).

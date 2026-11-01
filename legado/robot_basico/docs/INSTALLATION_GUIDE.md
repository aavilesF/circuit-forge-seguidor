# Guía de instalación (laptop)

**Sistema operativo:** no se pudo detectar (el enlace con la computadora de Alejandro no estaba disponible). La guía cubre Windows, macOS y Linux.
**Regla:** instala solo lo marcado *Competir* o *Desarrollo*. Lo de *Nivel B* es para después del 21 de noviembre.

Las URLs son las páginas oficiales de cada proyecto. La URL del gestor de placas del ESP32 está tomada de la documentación de Espressif; desde el entorno donde se escribió esta guía no se pudo abrir (red bloqueada), así que se confirma en el paso 4.

## 1. Tabla de software

| Software | Versión recomendada | Función | Obligatorio/opcional | Enlace oficial | Dependencias | Configuración | Prueba de verificación |
|---|---|---|---|---|---|---|---|
| Arduino IDE | 2.x (última estable) | Compilar y subir el firmware al ESP32 | **Competir** | https://www.arduino.cc/en/software | — | Agregar URL de placas ESP32 (paso 4) | Abre y lista "ESP32 Dev Module" |
| Core arduino-esp32 (Espressif) | 3.x estable (el firmware también acepta 2.x) | Toolchain, librerías del ESP32 | **Competir** | https://docs.espressif.com/projects/arduino-esp32/en/latest/installing.html | Arduino IDE | Gestor de placas → "esp32 by Espressif Systems" | Compila `seguidor.ino` sin errores |
| Driver USB-serie | El que corresponda al chip de la placa (ver paso 3) | Que la PC vea el ESP32 | **Competir** (Windows/macOS) | CP210x: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers · CH340/CH9102: https://www.wch-ic.com/downloads/ | — | Instalar y reconectar | Aparece un puerto COM / `/dev/cu.*` / `/dev/ttyUSB*` |
| Git | ≥ 2.30 | Clonar y subir el repositorio | **Competir** | https://git-scm.com/downloads | — | `git config --global user.name/user.email` | `git --version` |
| Python | ≥ 3.10 | Diagramas y regresión | Desarrollo | https://www.python.org/downloads/ | — | Marcar "Add to PATH" en Windows | `python3 --version` |
| numpy + matplotlib | últimas | Gráficas del simulador | Desarrollo | https://pypi.org/project/matplotlib/ | Python | `pip install numpy matplotlib` | `python3 herramientas/generar_diagramas.py` |
| Compilador C++17 (g++ ≥ 9 o clang) | — | Pruebas y simulador en la laptop | Desarrollo | Linux: paquete `build-essential` · macOS: `xcode-select --install` · Windows: WSL (https://learn.microsoft.com/windows/wsl/install) | — | En Windows usar la terminal de Ubuntu (WSL) | `g++ --version` y `pruebas/ejecutar.sh` |
| cppcheck | ≥ 2.10 | Análisis estático | Opcional | https://cppcheck.sourceforge.io/ (o `pip install cppcheck`) | Python (vía pip) | — | `cppcheck --version` |
| VS Code + PlatformIO IDE | últimas | Editor y alternativa a Arduino IDE (`firmware/platformio.ini`) | Opcional | https://code.visualstudio.com/ · https://platformio.org/install/ide?install=vscode | — | Abrir la carpeta `firmware/` | `pio run` compila |
| KiCad | 8 o 9 | PCB propia | **Nivel B** (C6) | https://www.kicad.org/download/ | — | — | Abre un proyecto de ejemplo |
| CAD (FreeCAD/Fusion/Onshape) | — | Chasis paramétrico | **Nivel B** | https://www.freecad.org/downloads.php | — | — | — |

No hace falta: ESP-IDF (usamos el core de Arduino), librerías de terceros (el firmware solo usa `Preferences.h`, que viene con el core), ni programas de telemetría inalámbrica (prohibida en competencia).

## 2. Orden de instalación

1. Git → 2. Arduino IDE → 3. driver USB → 4. core ESP32 → 5. clonar repo → 6. **primera compilación** → 7. Python y compilador C++ (para pruebas y simulador).
Los pasos 1-6 bastan para competir. Hazlos **antes** de que lleguen las piezas: la compilación no necesita el ESP32 conectado.

## 3. Driver USB
Mira el chip junto al conector USB de la placa: **CP2102/CP2104** → driver de Silicon Labs; **CH340/CH9102** → driver de WCH. En Linux no hace falta driver; agrega tu usuario al grupo `dialout` (`sudo usermod -aG dialout $USER`, cerrar sesión).
Usa un cable USB **de datos** (muchos cables solo cargan).

## 4. Core del ESP32 en Arduino IDE
1. *File → Preferences → Additional boards manager URLs*: `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
   (confirma la URL en la página de instalación de Espressif enlazada en la tabla).
2. *Tools → Board → Boards Manager* → buscar **esp32** → instalar "esp32 by Espressif Systems". Anota la versión instalada.
3. *Tools → Board → esp32 → **ESP32 Dev Module***. Ajustes: Upload Speed 921600 (si falla, 115200), CPU 240 MHz, Flash 4 MB, Partition Scheme "Default".

## 5. Clonar el repositorio
```bash
git clone https://github.com/aavilesF/circuit-forge-seguidor.git
cd circuit-forge-seguidor
git checkout engineering/final-prototype     # rama de trabajo actual
```

## 6. Primera compilación real (hallazgo H01 — la más importante)
1. Arduino IDE → *File → Open* → `firmware/seguidor/seguidor.ino` (la carpeta debe llamarse `seguidor`; el IDE abre también los `.cpp` y `.h`).
2. Botón **Verify** (✓). Sin placa conectada.
3. **Si compila:** anota en `modificaciones/` la versión del core y el uso de memoria que muestra el IDE. Eso cambia el estado a `[Compilado: no verificado en hardware]`.
4. **Si falla:** copia el mensaje completo a `modificaciones/AAAA-MM-DD-compilacion.md` y súbelo; es esperable (el código solo se probó contra un stub).
   Errores más probables: nombres del API de PWM (`ledcAttach`/`ledcWrite`) o de atenuación del ADC según la versión del core.

Alternativa PlatformIO: `cd firmware && pio run` (primera vez descarga la plataforma).

## 7. Pruebas y simulador en la laptop
```bash
pruebas/ejecutar.sh          # 93 pruebas de lógica
pruebas/regresion.sh         # todo: pruebas, sanitizers, cppcheck, sintaxis, escenarios
sim/ejecutar.sh              # una corrida
sim/ejecutar.sh modo=comparar vbase=0.6 > comparar.csv
python3 herramientas/generar_diagramas.py
```
Windows: ejecuta estos comandos dentro de WSL (Ubuntu). Los sanitizers no funcionan en MinGW; en WSL sí.
Variables de entorno: ninguna obligatoria. En WSL, si `python3` no encuentra matplotlib: `pip install --user numpy matplotlib`.

## 8. Subir al ESP32 y probar
1. Conecta la placa por USB (sin batería la primera vez). *Tools → Port* → el puerto nuevo.
2. **Upload**. Si se queda en "Connecting....", mantén presionado **BOOT** hasta que empiece a escribir.
3. *Tools → Serial Monitor* a **115200** baud, fin de línea "Newline". Debe aparecer "Circuit Forge - seguidor listo". Escribe `ayuda`.
4. Desde aquí sigue `docs/PROTOCOLO_PRUEBAS.md`.

## 9. Verificación final (marca cada una)
- [ ] `git --version`, `python3 --version`, `g++ --version` responden.
- [ ] Arduino IDE compila `seguidor.ino` (anotar versión del core).
- [ ] La placa aparece como puerto y recibe el firmware.
- [ ] El monitor serie muestra el mensaje de inicio.
- [ ] `pruebas/regresion.sh` termina con "REGRESIÓN COMPLETA: OK".

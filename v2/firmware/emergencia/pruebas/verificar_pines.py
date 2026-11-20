"""Compara los pines de emergencia/config.h con el esquema vigente del prototipo de emergencia.

Lee del propio esquema (robot_emergencia_unificado.kicad_sch) los nombres de pin del símbolo del ESP32
(número de pata del DevKit -> GPIO) y del netlist esperado (.esperado.json) qué red llega a cada pata de A1.
Así, si alguien cambia un pin en el esquema o en config.h, la prueba falla.

Uso:  python verificar_pines.py      (sale con código 1 si hay diferencias)
"""
import json
import pathlib
import re
import sys

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]                                   # .../v2
ESQ = RAIZ / "electronica" / "prototipo-emergencia" / "robot_emergencia_unificado.kicad_sch"
ESPERADO = ESQ.with_name(ESQ.name + ".esperado.json")
CONFIG = AQUI.parent / "emergencia" / "config.h"

# red del esquema -> macro de config.h
RED_A_MACRO = {
    "SIG": "PIN_MUX_SIG", "S0": "PIN_MUX_S0", "S1": "PIN_MUX_S1", "S2": "PIN_MUX_S2", "S3": "PIN_MUX_S3",
    "EMIT_EN": "PIN_EMISORES", "START": "PIN_START", "CAL": "PIN_CAL", "VBAT_SENSE": "PIN_BATERIA",
    "DRV_SLEEP": "PIN_NSLEEP", "AIN1": "PIN_AIN1", "AIN2": "PIN_AIN2", "BIN1": "PIN_BIN1", "BIN2": "PIN_BIN2",
}
PROHIBIDAS = ["PIN_ZUMBADOR", "PIN_NFAULT", "PIN_VENTILADOR", "PIN_FAN", "CANAL_ZUMB"]


def gpio_por_pata(texto: str) -> dict:
    """Número de pata del símbolo ESP32-DevKit-USB-C -> número de GPIO (de nombres como 'ADC2_CH0/GPIO4')."""
    m = re.search(r'\(symbol\s+"Simbolos:ESP32-DevKit-USB-C"', texto)
    if not m:
        raise SystemExit("no se encontró el símbolo Simbolos:ESP32-DevKit-USB-C en el esquema")
    sig = re.compile(r'\(symbol\s+"Simbolos:').search(texto, m.end())
    bloque = texto[m.start(): sig.start() if sig else len(texto)]
    patas = {}
    for nombre, numero in re.findall(r'\(name\s+"([^"]*)".*?\(number\s+"([^"]*)"', bloque, re.S):
        m = re.search(r"GPIO(\d+)", nombre)
        if m:
            patas[numero] = int(m.group(1))
        elif "SENSOR_VP" in nombre or nombre.endswith("VP"):
            patas[numero] = 36
        elif "SENSOR_VN" in nombre or nombre.endswith("VN"):
            patas[numero] = 39
    return patas


def macros(texto: str) -> dict:
    return {k: v for k, v in re.findall(r"^#define\s+(\w+)\s+(\S+)", texto, re.M)}


def main() -> int:
    errores = []
    esq = ESQ.read_text(encoding="utf-8")
    patas = gpio_por_pata(esq)
    netlist = json.loads(ESPERADO.read_text(encoding="utf-8"))
    red_por_pata = {pata: red for ref, pata, red in netlist["esperado"] if ref == "A1"}
    nc = {pata for ref, pata in netlist["nc"] if ref == "A1"}
    cfg = macros(CONFIG.read_text(encoding="utf-8"))

    vistas = set()
    for pata, red in sorted(red_por_pata.items(), key=lambda x: int(x[0])):
        if red not in RED_A_MACRO:
            continue                                     # alimentación / GND
        vistas.add(red)
        macro = RED_A_MACRO[red]
        gpio = patas.get(pata)
        valor = cfg.get(macro)
        if gpio is None:
            errores.append(f"la pata {pata} ({red}) no tiene GPIO en el símbolo")
        elif valor is None or int(valor) != gpio:
            errores.append(f"{red}: esquema = GPIO{gpio} (pata {pata}), config.h {macro} = {valor}")
        else:
            print(f"  ok  {red:10s} pata {pata:>2s} -> GPIO{gpio:<2d} = {macro}")
    for red in RED_A_MACRO:
        if red not in vistas:
            errores.append(f"la red {red} no llega al ESP32 en el esquema")
    for m in PROHIBIDAS:
        if m in cfg:
            errores.append(f"config.h define {m}: ese hardware no existe en el prototipo de emergencia")
    # el LED integrado (GPIO2) debe estar libre en el esquema
    pata_led = next((p for p, g in patas.items() if g == int(cfg.get("PIN_LED", -1))), None)
    if pata_led is not None and pata_led not in nc:
        errores.append(f"PIN_LED (GPIO{cfg['PIN_LED']}) está conectado en el esquema (pata {pata_led})")
    # canales del mux: SEN1..SEN8 en C0..C7
    for ref, pata, red in netlist["esperado"]:
        if ref == "U4" and pata.startswith("C") and pata[1:].isdigit():
            if red != f"SEN{int(pata[1:]) + 1}":
                errores.append(f"mux {pata} -> {red} (se esperaba SEN{int(pata[1:]) + 1})")
    if int(cfg.get("NUM_SENSORES", 0)) != sum(1 for r, p, _ in netlist["esperado"] if r == "U4" and p[:1] == "C"):
        errores.append("NUM_SENSORES no coincide con los canales conectados del mux")

    if errores:
        print("DIFERENCIAS entre config.h y el esquema:")
        for e in errores:
            print("  -", e)
        return 1
    print(f"pines: config.h coincide con {ESQ.name} ({len(vistas)} señales, LED en pata libre, mux C0..C7)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

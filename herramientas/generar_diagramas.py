#!/usr/bin/env python3
"""Genera los diagramas y las gráficas del proyecto.

Fuente de verdad de los pines: firmware/seguidor/pines.h (se lee con regex).
Salida: docs/diagramas/*.svg|png y docs/diagramas/pines.md
Uso: python3 herramientas/generar_diagramas.py
"""
import csv, math, re, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

RAIZ = Path(__file__).resolve().parent.parent
OUT = RAIZ / "docs" / "diagramas"
OUT.mkdir(parents=True, exist_ok=True)
RES = RAIZ / "sim" / "resultados"

# Paleta sobria (azul/naranja distinguibles en daltonismo) + neutros
AZUL, NARANJA, VERDE, GRIS, TINTA, ROJO = "#2a6fb0", "#d9792b", "#3a8f5c", "#9aa0a6", "#202124", "#c0392b"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.edgecolor": GRIS, "axes.labelcolor": TINTA,
                     "text.color": TINTA, "xtick.color": TINTA, "ytick.color": TINTA})

def guardar(fig, nombre):
    fig.savefig(OUT / f"{nombre}.svg", bbox_inches="tight")
    fig.savefig(OUT / f"{nombre}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("ok", nombre)

# ------------------------------------------------------------------ pines (desde pines.h)
txt = (RAIZ / "firmware/seguidor/pines.h").read_text(encoding="utf-8")
PIN = {m.group(1): int(m.group(2)) for m in re.finditer(r"constexpr int\s+(PIN_\w+)\s*=\s*(\d+)", txt)}
DESTINO = {
 "PIN_MUX_S0": ("Dirección S0 de los multiplexores", "Salida"), "PIN_MUX_S1": ("Dirección S1", "Salida"),
 "PIN_MUX_S2": ("Dirección S2", "Salida"), "PIN_MUX_S3": ("Dirección S3", "Salida"),
 "PIN_MUX_SIG1": ("SIG del multiplexor 1 (canales 0-15)", "Solo entrada, ADC1"),
 "PIN_MUX_SIG2": ("SIG del multiplexor 2 (canales 16-23); sin conectar con 8 sensores", "Solo entrada, ADC1"),
 "PIN_EMISORES": ("Compuerta del MOSFET de los LED IR (con resistencia a GND)", "Salida"),
 "PIN_PWMA": ("TB6612 PWMA (rueda izquierda)", "PWM 20 kHz"), "PIN_AIN1": ("TB6612 AIN1", "Salida"),
 "PIN_AIN2": ("TB6612 AIN2", "Salida"), "PIN_PWMB": ("TB6612 PWMB (rueda derecha)", "PWM 20 kHz"),
 "PIN_BIN1": ("TB6612 BIN1", "Salida"), "PIN_BIN2": ("TB6612 BIN2", "Salida"), "PIN_STBY": ("TB6612 STBY", "Salida (bajo = motores libres)"),
 "PIN_START": ("Botón START a GND", "Pull-up interno"), "PIN_CAL": ("Botón CAL a GND", "Pull-up interno"),
 "PIN_LED": ("LED de estado", "Salida (pin de arranque: no forzar al encender)"),
 "PIN_PERFIL": ("Perilla de perfil de velocidad (centro del potenciómetro, extremos a 3V3 y GND)", "Solo entrada, ADC1"),
 "PIN_BATERIA": ("Divisor de batería 100k/47k (punto medio)", "Solo entrada, ADC1"),
}
ORDEN = list(DESTINO)
faltan = [k for k in ORDEN if k not in PIN]
if faltan: sys.exit(f"pines.h no define: {faltan}")
usados = [PIN[k] for k in ORDEN]
dup = {p for p in usados if usados.count(p) > 1}
if dup: sys.exit(f"GPIO repetidos: {sorted(dup)}")
PROHIBIDOS = {6, 7, 8, 9, 10, 11}           # flash interna
ARRANQUE = {0, 2, 5, 12, 15}                # pines de arranque (strapping)
SOLO_ENTRADA = {34, 35, 36, 39}
for k in ORDEN:
    p = PIN[k]
    if p in PROHIBIDOS: sys.exit(f"{k}=GPIO{p} esta conectado a la flash")
    if p in SOLO_ENTRADA and "Solo entrada" not in DESTINO[k][1]: sys.exit(f"{k}=GPIO{p} es solo entrada")
    if "Solo entrada" in DESTINO[k][1] and p not in SOLO_ENTRADA and p not in {32, 33, 36, 39, 34, 35}:
        sys.exit(f"{k} debe ser ADC1")
    if p in {0, 12, 15, 5}: sys.exit(f"{k}=GPIO{p} es pin de arranque delicado")

filas = ["| Señal (pines.h) | GPIO | Conexión | Nota |", "|---|---|---|---|"]
for k in sorted(ORDEN, key=lambda k: PIN[k]):
    filas.append(f"| `{k}` | {PIN[k]} | {DESTINO[k][0]} | {DESTINO[k][1]} |")
(OUT / "pines.md").write_text("<!-- Generado por herramientas/generar_diagramas.py desde firmware/seguidor/pines.h. No editar a mano. -->\n\n" + "\n".join(filas) + "\n", encoding="utf-8")
print("ok pines.md (", len(ORDEN), "señales, sin repetidos)")

# ------------------------------------------------------------------ diagrama de bloques
def caja(ax, x, y, w, h, t, color, sub=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc="white", ec=color, lw=2))
    ax.text(x + w/2, y + h/2 + (0.12 if sub else 0), t, ha="center", va="center", fontsize=10, fontweight="bold")
    if sub: ax.text(x + w/2, y + h/2 - 0.2, sub, ha="center", va="center", fontsize=7.5, color="#555")

def flecha(ax, a, b, color, txt=None, dy=0.0):
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="-|>", color=color, lw=1.8))
    if txt: ax.text((a[0]+b[0])/2, (a[1]+b[1])/2 + 0.12 + dy, txt, ha="center", fontsize=7.5, color=color)

fig, ax = plt.subplots(figsize=(12, 6.2)); ax.set_xlim(0, 12); ax.set_ylim(0, 6.2); ax.axis("off")
ax.set_title("Diagrama de bloques: energía (naranja) y señales (azul)", loc="left", fontsize=12, fontweight="bold")
caja(ax, 0.2, 2.6, 1.8, 1.2, "Batería LiPo 2S", NARANJA, "7.4 V (6.6-8.4 V)")
caja(ax, 2.5, 2.6, 1.5, 1.2, "Fusible\nreseteable", NARANJA, "en serie con +")
caja(ax, 4.6, 3.6, 1.7, 1.0, "Buck 6 V", NARANJA, "motores")
caja(ax, 4.6, 1.4, 1.7, 1.0, "Buck 5 V", NARANJA, "VIN del ESP32")
caja(ax, 7.0, 1.2, 2.0, 1.2, "ESP32 DevKit", AZUL, "3.3 V lógica")
caja(ax, 7.0, 3.4, 2.0, 1.2, "TB6612FNG", AZUL, "VM=6 V, VCC=3.3 V")
caja(ax, 10.1, 4.1, 1.6, 0.9, "Motor izq.\nN20", VERDE); caja(ax, 10.1, 2.9, 1.6, 0.9, "Motor der.\nN20", VERDE)
caja(ax, 7.0, -0.4, 2.2, 1.0, "2× CD74HC4067", AZUL, "multiplexores")
caja(ax, 10.1, -0.4, 1.6, 1.0, "Sensores IR", AZUL, "8 o 24 canales")
caja(ax, 10.1, 1.3, 1.6, 1.1, "START, CAL,\nLED, perilla", GRIS)
flecha(ax, (2.0, 3.2), (2.5, 3.2), NARANJA)
flecha(ax, (4.0, 3.5), (4.6, 4.1), NARANJA); flecha(ax, (4.0, 2.9), (4.6, 1.9), NARANJA)
flecha(ax, (6.3, 4.1), (7.0, 4.0), NARANJA, "6 V"); flecha(ax, (6.3, 1.9), (7.0, 1.8), NARANJA, "5 V")
flecha(ax, (8.0, 2.4), (8.0, 3.4), AZUL); ax.text(8.1, 2.9, "PWM, AIN/BIN, STBY", fontsize=7.5, color=AZUL)
flecha(ax, (9.0, 4.2), (10.1, 4.5), VERDE); flecha(ax, (9.0, 3.7), (10.1, 3.35), VERDE)
flecha(ax, (8.0, 1.2), (8.0, 0.6), AZUL); ax.text(8.1, 0.8, "S0-S3, SIG1/2", fontsize=7.5, color=AZUL)
flecha(ax, (9.2, 0.1), (10.1, 0.1), AZUL); flecha(ax, (10.9, 1.3), (9.0, 1.8), GRIS)
ax.set_ylim(-0.6, 6.2)
ax.text(0.2, -0.5, "Regla: todo lo que toque un pin del ESP32 trabaja a 3.3 V\n(los sensores también se alimentan a 3.3 V).\nTierras (GND) unidas en un solo punto cerca de la batería.\nLos LED IR van por MOSFET, no directo de un pin.",
        fontsize=8.5, color="#444", va="bottom")
guardar(fig, "01_bloques")

# ------------------------------------------------------------------ cableado (tabla de pines)
fig, ax = plt.subplots(figsize=(11.5, 0.42 * (len(ORDEN) + 2))); ax.axis("off")
ax.set_title("Cableado del ESP32 (generado desde pines.h)", loc="left", fontsize=12, fontweight="bold")
rows = [[f"GPIO{PIN[k]}", k.replace("PIN_", ""), DESTINO[k][0]] for k in sorted(ORDEN, key=lambda k: PIN[k])]
t = ax.table(cellText=rows, colLabels=["Pin", "Señal", "Conecta a"], loc="center", cellLoc="left", colWidths=[0.09, 0.14, 0.77])
t.auto_set_font_size(False); t.set_fontsize(8.5); t.scale(1, 1.45)
for (r, c), cell in t.get_celld().items():
    cell.set_edgecolor("#ddd")
    if r == 0: cell.set_facecolor("#e8eef5"); cell.set_text_props(fontweight="bold")
guardar(fig, "02_cableado")

# ------------------------------------------------------------------ vista superior a escala
def vista_superior(perfil):
    n24 = perfil == 24
    fig, ax = plt.subplots(figsize=(9.5, 6.2))
    # marco: x lateral (mm), y hacia adelante; eje de ruedas en y=0
    piezas = {  # nombre: (cx, cy, ancho_x, largo_y, color)
        "Batería 2S": (0, 25, 50, 25, NARANJA),
        "Bucks": (0, 50, 40, 17, NARANJA),
        "TB6612": (0, -22, 20, 20, AZUL),
        "ESP32": (0, -52, 55, 28, AZUL),
        "Multiplexores": (0, 70, 36, 18, AZUL),
        "Motor izq.": (-17.5, 0, 30, 12, VERDE),
        "Motor der.": (17.5, 0, 30, 12, VERDE),
    }
    ancho_barra = 100 if n24 else 75
    piezas["Sensores (24)" if n24 else "Sensores (QTR-8A)"] = (0, 95 if n24 else 100, ancho_barra, 22 if n24 else 13, ROJO)
    ax.add_patch(Rectangle((-50, -85), 100, 200, fill=False, ls="--", ec=GRIS, lw=1.2))   # referencia 10x20 cm
    for nombre, (cx, cy, w, l, col) in piezas.items():
        ax.add_patch(Rectangle((cx - w/2, cy - l/2), w, l, fc=col, alpha=0.25, ec=col, lw=1.5))
        ax.text(cx, cy + (8 if nombre.startswith("Sensores") else 0), nombre, ha="center", va="center", fontsize=7.5)
    for s in (-1, 1):
        ax.add_patch(Rectangle((s * 37.5 - 5, -16.5), 10, 33, fc=TINTA, alpha=0.8))     # rueda 33 mm de diámetro, 10 de ancho
    ax.add_patch(Circle((0, -80), 5, fc=GRIS, ec=TINTA))                                   # ball caster
    ax.text(9, -80, "caster", ha="left", va="center", fontsize=7)
    # sensores
    if n24:
        for i in range(24):
            th = (i - 11.5) * 4.0 / 80.0
            ax.plot(80 * math.sin(th), 100 - 80 + 80 * math.cos(th), "o", ms=2, color=ROJO)
    else:
        for i in range(8):
            ax.plot((i - 3.5) * 9.525, 100, "o", ms=3.5, color=ROJO)
    # medidas
    xs = [c[0] - c[2]/2 for c in piezas.values()] + [c[0] + c[2]/2 for c in piezas.values()] + [-42.5, 42.5]
    ys = [c[1] - c[3]/2 for c in piezas.values()] + [c[1] + c[3]/2 for c in piezas.values()] + [-85]
    ancho, largo = max(xs) - min(xs), max(ys) - min(ys)
    ok = ancho <= 100 and largo <= 200
    ax.set_xlim(-70, 70); ax.set_ylim(-95, 125); ax.set_aspect("equal")
    ax.annotate("", xy=(60, 100), xytext=(60, 0), arrowprops=dict(arrowstyle="<->", color=TINTA))
    ax.text(62, 50, "100 mm\neje→sensores", fontsize=7.5, va="center")
    ax.set_xlabel("mm (x: derecha)"); ax.set_ylabel("mm (y: adelante, eje de ruedas en 0)")
    ax.set_title(f"Vista superior a escala - perfil {'curvo 24' if n24 else 'QTR-8A'}  |  ocupa {ancho:.0f} × {largo:.0f} mm (límite 100 × 200): {'CABE' if ok else 'NO CABE'}",
                 loc="left", fontsize=10.5, fontweight="bold")
    ax.text(-68, -93, "Medidas NOMINALES de piezas: cambiar con las reales al comprarlas.", fontsize=7.5, color="#555")
    ax.grid(alpha=0.2)
    guardar(fig, f"03_vista_superior_{perfil}")
    return ancho, largo, ok

medidas = {p: vista_superior(p) for p in (8, 24)}
with open(OUT / "medidas.txt", "w") as f:
    for p, (a, l, ok) in medidas.items(): f.write(f"perfil {p}: {a:.1f} x {l:.1f} mm, cabe={ok}\n")

# ------------------------------------------------------------------ gráficas de simulación
def leer(path):
    with open(path) as f: return list(csv.DictReader(l for l in f if not l.startswith("#")))

def graf_traza(nombre, titulo):
    t = RES / f"{nombre}.csv"
    if not t.exists(): return
    tr, pista = leer(t), leer(str(t) + ".pista.csv")
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 8.5), gridspec_kw={"height_ratios": [2.2, 1]})
    a1.plot([float(r["x"]) for r in pista], [float(r["y"]) for r in pista], color="#222", lw=9, alpha=0.85, solid_capstyle="butt", label="Línea (25 mm)")
    a1.plot([float(r["x"]) for r in tr], [float(r["y"]) for r in tr], color=NARANJA, lw=1.5, label="Eje del robot")
    a1.set_aspect("equal"); a1.set_title(titulo, loc="left", fontweight="bold"); a1.legend(loc="upper right"); a1.set_xlabel("mm"); a1.set_ylabel("mm")
    tt = [float(r["t"]) for r in tr]
    a2.plot(tt, [float(r["err"]) for r in tr], color=AZUL, lw=1.2)
    a2.set_xlabel("tiempo (s)"); a2.set_ylabel("error real (mm)"); a2.grid(alpha=0.25)
    a2.set_title("Distancia de la barra de sensores a la línea", loc="left", fontsize=9)
    guardar(fig, "sim_" + nombre)

graf_traza("base8", "Simulación: QTR-8A, kp=0.04 kd=0.002 vbase=0.40")
graf_traza("base24", "Simulación: curvo de 24, kp=0.04 kd=0.002 vbase=0.40")

b8, b24 = RES / "barrido_vbase_8.csv", RES / "barrido_vbase_24.csv"
if b8.exists() and b24.exists():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    for arch, col, lab in ((b8, AZUL, "QTR-8A"), (b24, NARANJA, "Curvo 24")):
        d = [r for r in leer(arch) if r["fin"] == "meta"]
        v = [float(r["vmedia"]) / 1000 for r in d]
        a1.plot(v, [float(r["tiempo"]) for r in d], color=col, lw=2); a1.text(v[-1], float(d[-1]["tiempo"]), " " + lab, color=col, va="center", fontsize=9)
        a2.plot(v, [float(r["err_medio"]) for r in d], color=col, lw=2); a2.text(v[-1], float(d[-1]["err_medio"]), " " + lab, color=col, va="center", fontsize=9)
    a1.set_xlabel("velocidad media (m/s)"); a1.set_ylabel("tiempo en la pista (s)"); a1.set_title("Más velocidad, menos tiempo", loc="left", fontsize=10, fontweight="bold")
    a2.set_xlabel("velocidad media (m/s)"); a2.set_ylabel("error medio (mm)"); a2.set_title("pero crece el error", loc="left", fontsize=10, fontweight="bold")
    for a in (a1, a2): a.grid(alpha=0.25); a.set_xlim(right=1.45)
    fig.text(0.01, -0.04, "El modelo NO simula derrape: arriba de ~0.9 m/s en curvas de 15 cm la aceleración lateral pasa de ~0.9 g, así que esos puntos no son confiables.", fontsize=8, color="#555")
    guardar(fig, "sim_velocidad")

import csv, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from modelo import pistas_reglamento
OUT = "../../docs/speed-follower/"
P = pistas_reglamento()
fig, axs = plt.subplots(1, 3, figsize=(15, 3.6))
for a, p in zip(axs, P):
    a.add_patch(plt.Rectangle((0, 0), 2.44, 1.22, fill=False, ec="gray", ls="--"))
    a.plot(p.xy[:, 0], p.xy[:, 1], color="#222", lw=3); a.plot(p.xy[p.hueco, 0], p.xy[p.hueco, 1], "o", color="#d9792b", ms=5)
    a.set_aspect("equal"); a.set_title(f"{p.nombre} · {p.largo:.2f} m", fontsize=9, loc="left"); a.set_xlim(-0.05, 2.5); a.set_ylim(-0.05, 1.3)
fig.suptitle("Pistas de prueba (ejemplos que cumplen el reglamento; la pista real es desconocida). Naranja: huecos de 5 mm", fontsize=10, x=0.01, ha="left")
fig.savefig(OUT + "pistas_prueba.png", dpi=110, bbox_inches="tight"); plt.close(fig)

rows = list(csv.DictReader(open("resultados/S8_cuello_inercia.csv")))
fig, a = plt.subplots(figsize=(7.5, 4))
cols = {"80": "#9aa0a6", "100": "#7aa6d6", "120": "#2a6fb0", "140": "#d9792b", "160": "#8e5bb5"}
for L in ("80", "100", "120", "140", "160"):
    d = [r for r in rows if r["L_mm"] == L]
    xs = [float(r["v_max"]) for r in d]; ys = [int(r["exitos_de_9"]) for r in d]
    a.plot(xs, ys, "-o", color=cols[L], lw=2, ms=5, label=f"L = {L} mm")
a.set_xlabel("velocidad máxima pedida (m/s)"); a.set_ylabel("vueltas completas de 9 (3 pistas × 3 semillas)")
a.set_title("Cuello L con inercia realista: 120-160 mm sostienen 1.2 m/s", loc="left", fontsize=10, fontweight="bold")
a.grid(alpha=0.25); a.set_xlim(0.95, 1.45); a.set_ylim(0, 9.5); a.legend(loc="lower left", fontsize=8, frameon=False)
fig.savefig(OUT + "cuello_vs_velocidad.png", dpi=110, bbox_inches="tight"); plt.close(fig)
print("ok")

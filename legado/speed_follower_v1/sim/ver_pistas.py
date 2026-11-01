import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from modelo import pistas_reglamento
P = pistas_reglamento()
fig, axs = plt.subplots(1, 3, figsize=(15, 3.6))
for a, p in zip(axs, P):
    a.add_patch(plt.Rectangle((0, 0), 2.44, 1.22, fill=False, ec="gray", ls="--"))
    a.plot(p.xy[:, 0], p.xy[:, 1], "k", lw=3)
    a.plot(p.xy[p.hueco, 0], p.xy[p.hueco, 1], "r.", ms=6)
    a.set_aspect("equal"); a.set_title(f"{p.nombre} · {p.largo:.2f} m", fontsize=9); a.set_xlim(-0.05, 2.5); a.set_ylim(-0.05, 1.3)
fig.savefig("/tmp/claude-0/-home-claude/c426ef1d-2801-53b8-a19a-5de029d74a00/scratchpad/pistas.png", dpi=90, bbox_inches="tight")
for p in P: print(p.nombre, p.xy.min(0).round(2), p.xy.max(0).round(2))

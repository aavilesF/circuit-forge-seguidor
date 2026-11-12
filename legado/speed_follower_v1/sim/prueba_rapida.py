import time
from modelo import Robot, MOTORES, pistas_reglamento
from control import ControlSF, ParamSF, ControlDuty, ParamDuty
from simular import correr
P = pistas_reglamento()
for p in P: print(p.nombre, f"{p.largo:.2f} m", "cerrada" if p.cerrada else "abierta", p.xy.min(0).round(2), p.xy.max(0).round(2))
r = Robot(MOTORES["Pololu HPCB 12V 10:1"], v_bat=7.4)
t0 = time.time()
for p in P:
    res = correr(r, p, lambda: ControlSF(ParamSF(v_max=1.5)))
    print(p.nombre, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in res.items()})
print("seg", time.time() - t0)

"""¿Ayuda el freno activo? python3 freno_activo.py -> resultados/S9_freno_activo.csv"""
import csv, math
from multiprocessing import Pool
from modelo import Robot, MOTORES, pistas_reglamento
from control import ControlSF, ParamSF
from simular import correr
P = pistas_reglamento()
def J(L): return 3.3e-4 + 0.010 * L * L + 0.008 * L * L / 3
def f(a):
    motor, fa, vm = a
    m = MOTORES[motor]
    r = Robot(m, v_bat=7.4, v_max_motor=6.0 if m.v_nom == 6 else 99, L=0.13, n_sens=8, paso=0.0095, radio_giro=math.sqrt(J(0.13) / 0.2))
    res = [correr(r, p, lambda: ControlSF(ParamSF(v_max=vm, kp=120, kd=4, a_lat=4.0, freno_activo=fa)), t_max=25, semilla=s) for p in P for s in (1, 2, 3)]
    ok = sum(x["ok"] for x in res)
    t = sum(x["t"] for x in res if x["ok"]) / max(ok, 1)
    return dict(motor=motor, freno_activo=fa, v_max=vm, exitos_de_9=ok, t_medio_vuelta=round(t, 2), t_reversa=round(sum(x["t_reversa"] for x in res), 3), i_pico=round(max(x["i_pico"] for x in res), 2))
if __name__ == "__main__":
    tareas = [(m, fa, v) for m in ("Pololu HPCB 12V 15:1", "Pololu HPCB 12V 10:1") for fa in (False, True) for v in (1.1, 1.2, 1.3, 1.4)]
    with Pool() as pool: filas = pool.map(f, tareas)
    with open("resultados/S9_freno_activo.csv", "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=list(filas[0].keys())); w.writeheader(); w.writerows(filas)
    for x in filas: print(x)

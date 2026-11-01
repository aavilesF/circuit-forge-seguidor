"""Barrido de parámetros del controlador SF para un robot dado. Uso: python3 barrido_control.py <motor> <vbat> <vmax_motor> <diam_mm> [salida.csv]"""
import sys, csv, itertools, math
from multiprocessing import Pool
from modelo import Robot, MOTORES, pistas_reglamento
from control import ControlSF, ParamSF
from simular import correr

P = pistas_reglamento()

def evalua(args):
    robot, prm = args
    tot, ok, emax, inv, rev = 0.0, 0, 0.0, 0.0, 0.0
    for p in P:
        r = correr(robot, p, lambda: ControlSF(prm), t_max=25)
        tot += r["t"] if r["ok"] else 99
        ok += r["ok"]; emax = max(emax, r["e_max"]); inv += r["t_inv"]; rev += r["t_reversa"]
    return dict(kp=prm.kp, kd=prm.kd, a_lat=prm.a_lat, v_max=prm.v_max, k_pp=prm.k_pp, ok=ok, t_total=round(tot, 3), e_max_mm=round(emax * 1000, 1), t_inv=round(inv, 3), t_reversa=round(rev, 3))

def grid(robot, kps=(60, 120, 200), kds=(2, 4, 8), alats=(4, 5), vmaxs=(1.0, 1.5, 2.0, 2.5), kpps=(1,)):
    tareas = [(robot, ParamSF(v_max=v, a_lat=a, kp=kp, kd=kd, k_pp=k)) for kp, kd, a, v, k in itertools.product(kps, kds, alats, vmaxs, kpps)]
    with Pool() as pool:
        return pool.map(evalua, tareas)

if __name__ == "__main__":
    m = MOTORES[sys.argv[1]]; vb = float(sys.argv[2]); vmm = float(sys.argv[3]); d = float(sys.argv[4]) / 1000
    res = grid(Robot(m, v_bat=vb, v_max_motor=vmm, diam=d))
    res.sort(key=lambda r: (-r["ok"], r["t_total"]))
    if len(sys.argv) > 5:
        with open(sys.argv[5], "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(res[0].keys())); w.writeheader(); w.writerows(res)
    for r in res[:8]: print(r)

"""Velocidad máxima sostenible: mayor v_max en la que se completan las 3 pistas con 3 semillas (9/9).
Uso: python3 robustez.py  -> resultados/S7_robustez.csv"""
import csv, itertools
from multiprocessing import Pool
from modelo import Robot, MOTORES, pistas_reglamento
from control import ControlSF, ParamSF
from simular import correr

P = pistas_reglamento()
VS = (0.9, 1.0, 1.1, 1.2, 1.3, 1.4)
CTRL = dict(kp=120, kd=4, a_lat=4.0)

def exitos(args):
    robot, vm = args
    n = 0
    for semilla in (1, 2, 3):
        for p in P:
            n += correr(robot, p, lambda: ControlSF(ParamSF(v_max=vm, **CTRL)), t_max=25, semilla=semilla)["ok"]
    return n

def tarea(robot):
    return [(robot, v) for v in VS]

if __name__ == "__main__":
    casos = []
    m15 = MOTORES["Pololu HPCB 12V 15:1"]
    for L, (n, pa) in itertools.product((0.10, 0.12, 0.14, 0.16), ((8, 0.0095), (12, 0.008), (16, 0.006))):
        casos.append((dict(motor=m15.nombre, L_mm=int(L * 1000), n=n, paso_mm=pa * 1000), Robot(m15, v_bat=7.4, L=L, n_sens=n, paso=pa)))
    for nombre in ("Pololu HPCB 12V 10:1", "Pololu HPCB 6V 15:1", "Pololu HP 6V 10:1", "GA12-N20 6V 1000RPM (supuesto)"):
        m = MOTORES[nombre]
        casos.append((dict(motor=nombre, L_mm=140, n=12, paso_mm=8.0), Robot(m, v_bat=7.4, v_max_motor=6.0 if m.v_nom == 6 else 99, L=0.14, n_sens=12, paso=0.008)))
    tareas = [t for _, r in casos for t in tarea(r)]
    with Pool() as pool:
        res = pool.map(exitos, tareas)
    filas = []
    for i, (et, _) in enumerate(casos):
        exs = res[i * len(VS):(i + 1) * len(VS)]
        vmax_ok = max([v for v, e in zip(VS, exs) if e == 9], default=0)
        fila = dict(et); fila.update({f"v{v}": e for v, e in zip(VS, exs)}); fila["v_sostenible"] = vmax_ok
        filas.append(fila)
    with open("resultados/S7_robustez.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys())); w.writeheader(); w.writerows(filas)
    for f_ in filas: print(f_)

"""Cuello L con inercia realista: J(L) = J_cuerpo + m_barra·L² + m_cuello·L²/3 (SUPUESTOS de masa, ver doc).
Uso: python3 cuello_inercia.py -> resultados/S8_cuello_inercia.csv"""
import csv, math
from multiprocessing import Pool
from modelo import Robot, MOTORES, pistas_reglamento
from control import ControlSF, ParamSF
from simular import correr
P = pistas_reglamento()
M = 0.20
J_CUERPO = 3.3e-4      # kg·m² (batería, motores y ruedas, ESP32, driver, chasis de 50 g, apoyo) [Estimado]
M_BARRA = 0.010        # kg barra de sensores + conector
M_CUELLO = 0.008       # kg estructura del cuello
def J(L): return J_CUERPO + M_BARRA * L * L + M_CUELLO * L * L / 3
def f(a):
    L, vm = a
    rg = math.sqrt(J(L) / M)
    r = Robot(MOTORES["Pololu HPCB 12V 15:1"], v_bat=7.4, L=L, n_sens=8, paso=0.0095, radio_giro=rg, masa=M)
    ok = sum(correr(r, p, lambda: ControlSF(ParamSF(v_max=vm, kp=120, kd=4, a_lat=4.0)), t_max=25, semilla=s)["ok"] for p in P for s in (1, 2, 3))
    return dict(L_mm=int(L * 1000), J_kgm2=f"{J(L):.2e}", radio_giro_mm=round(rg * 1000, 1), v_max=vm, exitos_de_9=ok)
if __name__ == "__main__":
    with Pool() as pool:
        filas = pool.map(f, [(L, v) for L in (0.08, 0.10, 0.12, 0.14, 0.16) for v in (1.0, 1.1, 1.2, 1.3, 1.4)])
    with open("resultados/S8_cuello_inercia.csv", "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=list(filas[0].keys())); w.writeheader(); w.writerows(filas)
    for x in filas: print(x)

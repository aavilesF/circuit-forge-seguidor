"""Carga config/robot_maestro.yaml y deriva todo lo que usan el simulador, la verificación y el
generador de cabecera del firmware. Ningún otro archivo debe repetir estos números."""
from __future__ import annotations

import math
import os
from dataclasses import dataclass, field, replace

import numpy as np
import yaml

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RUTA = os.path.join(RAIZ, "config", "robot_maestro.yaml")
G = 9.81
KGCM = 0.0980665


def cargar(ruta: str = RUTA) -> dict:
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass(frozen=True)
class Motor:
    clave: str
    nombre: str
    V_nom: float
    rpm: float
    T_bl: float
    I_bl: float
    I0: float
    G: float
    limite_V: float  # V máximo promedio aplicado (inf si no hay límite)

    @property
    def w0(self):
        return self.rpm * 2 * math.pi / 60

    @property
    def R(self):
        return self.V_nom / self.I_bl

    @property
    def Ke(self):
        return (self.V_nom - self.I0 * self.R) / self.w0

    @property
    def Kt(self):
        return self.T_bl / (self.I_bl - self.I0)


def motor(cfg: dict, clave: str, **cambios) -> Motor:
    """Motor del YAML. Si par_kgcm es null, el par de bloqueo se estima con T = eta·Ke·(I_bl − I0).
    cambios: I_bloqueo, rpm, eta (análisis de sensibilidad de los motores sin ficha)."""
    m = dict(cfg["motores"][clave]); m.update(cambios)
    V, rpm, Ib, I0 = m["V_nom"], m["rpm"], m["I_bloqueo"], m["I_vacio"]
    if m.get("par_kgcm") is None:
        R = V / Ib
        Ke = (V - I0 * R) / (rpm * 2 * math.pi / 60)
        T = m["eta"] * Ke * (Ib - I0)
    else:
        T = m["par_kgcm"] * KGCM
    return Motor(clave, m["nombre"], V, rpm, T, Ib, I0, m["relacion"], m["limite_V"] if m["limite_V"] else math.inf)


def sensores(cfg: dict, clave: str, L: float):
    """Posiciones (x, y) de cada sensor en el marco del cuerpo, de derecha (y<0) a izquierda."""
    b = cfg["barras"][clave]
    n, p = b["n"], b["paso"]
    k = np.arange(n) - (n - 1) / 2
    if b["tipo"] == "recta":
        return np.full(n, L), -k * p
    phi = -k * p / L          # paso medido sobre el arco de radio L centrado en el eje
    return L * np.cos(phi), L * np.sin(phi)


def masa_y_cg(cfg: dict, succion: bool, motor_clave: str | None = None, barra_clave: str | None = None):
    """Masa, x y z del CG e inercia de guiñada desde `componentes` (posiciones y medidas de la disposición).
    par: true reparte la masa en ±y; dim [lx, ly] agrega la inercia de una placa; Iz_propio la sustituye."""
    comp = {k: dict(v) for k, v in cfg["componentes"].items()}
    if motor_clave and "motores" in comp:  # la masa de motores (con encoder) sigue a la selección
        mm = cfg["motores"][motor_clave]
        comp["motores"]["masa"] = 2 * (mm["masa"] + mm.get("masa_encoder", 0.0))
    if barra_clave and "masa" in cfg["barras"][barra_clave] and "barra_sensores" in comp:
        comp["barra_sensores"]["masa"] = cfg["barras"][barra_clave]["masa"]
    if succion:
        comp["succion"] = dict(masa=cfg["succion"]["masa"], x=cfg["geometria"]["x_succion"], z=0.015)
    m = sum(c["masa"] for c in comp.values())
    x = sum(c["masa"] * c["x"] for c in comp.values()) / m
    z = sum(c["masa"] * c["z"] for c in comp.values()) / m
    Iz = 0.0
    for c in comp.values():
        y = c.get("y", 0.0)
        Iz += c["masa"] * ((c["x"] - x) ** 2 + y ** 2)
        if "Iz_propio" in c:
            Iz += c["Iz_propio"]
        elif "dim" in c:
            lx, ly = c["dim"]
            Iz += c["masa"] * (lx ** 2 + ly ** 2) / 12
    return m, x, z, Iz


@dataclass(frozen=True)
class Config:
    """Todo lo que necesita una corrida del simulador, ya derivado."""
    motor: Motor
    barra: str
    mcu: str
    control: str
    succion: bool
    masa: float
    x_cg: float
    h_cg: float
    Iz: float
    L: float
    W: float
    r: float
    x_apoyo: float
    x_succion: float
    F_succion: float
    mu: float
    c_rr: float
    eps: float
    mu_k_rel: float
    v_str: float
    desliz_valido: float
    J_eq: float
    V_oc: float
    R_int: float
    I_log: float
    I_fan: float
    sx: np.ndarray = field(compare=False)
    sy: np.ndarray = field(compare=False)
    mancha: float = 0.003
    ruido: float = 0.03
    umbral: float = 0.25
    t_lectura: float = 0.0
    T_ctrl: float = 0.001
    t_perdida: float = 0.3
    I_ocp: float = 2.0
    giro_ruido: float = 0.02
    giro_sesgo: float = 0.03
    ancho_linea: float = 0.025
    cpr_rueda: float = 0.0          # cuentas del encoder por vuelta de rueda (0 = sin encoder)
    prm: dict = field(default_factory=dict, compare=False)

    @property
    def f_motriz(self):
        """Fracción del peso estático sobre las ruedas (sin succión)."""
        return 1 - self.x_cg / self.x_apoyo


def construir(cfg: dict | None = None, **cambios) -> Config:
    """Arma la configuración vigente (sección `arquitectura`) con cambios opcionales:
    motor, barra, mcu, control, succion, L, mu, V_oc, ... y prm (dict de parámetros de control)."""
    cfg = cfg or cargar()
    arq = dict(cfg["arquitectura"])
    for k in ("motor", "barra", "mcu", "control", "succion"):
        if k in cambios:
            arq[k] = cambios.pop(k)
    mot = motor(cfg, arq["motor"], **cambios.pop("motor_cambios", {}))
    succ = bool(arq["succion"])
    m, x, z, Iz = masa_y_cg(cfg, succ, arq["motor"], arq["barra"])
    geo = cfg["geometria"]
    L = cambios.pop("L", geo["L_cuello"])
    sx, sy = sensores(cfg, arq["barra"], L)
    op = dict(cfg["optica"])
    for k in ("radio_mancha", "ruido", "resta_ambiente"):
        if k in cfg["barras"][arq["barra"]]:
            op[k] = cfg["barras"][arq["barra"]][k]
    mc = cfg["mcu"][arq["mcu"]]
    n = len(sx)
    n_conv = math.ceil(n / mc.get("n_adc", 1))      # conversiones en serie por ADC
    t_lect = ((2 * (n_conv * mc["t_canal"] + op["t_emisor"])) if op["resta_ambiente"] else n_conv * mc["t_canal"]) \
        + mc["t_calculo"]
    r = geo["D_llanta"] / 2
    J = cfg["J_rotor"] * mot.G ** 2 + cfg["J_llanta"]
    prm = dict(cfg["control"][arq["control"]])
    prm.update(cambios.pop("prm", {}))
    c = Config(
        motor=mot, barra=arq["barra"], mcu=arq["mcu"], control=arq["control"], succion=succ,
        masa=m, x_cg=x, h_cg=z, Iz=Iz, L=L, W=geo["W_via"], r=r, x_apoyo=geo["x_apoyo"],
        x_succion=geo["x_succion"], F_succion=(cfg["succion"]["F_down_gf"] / 1000 * G if succ else 0.0),
        mu=cfg["traccion"]["mu"], c_rr=cfg["traccion"]["c_rodadura"], eps=cfg["traccion"]["eps_deslizamiento"],
        mu_k_rel=cfg["traccion"]["mu_cinetico_rel"], v_str=cfg["traccion"]["v_stribeck"],
        desliz_valido=cfg["traccion"]["desliz_valido"],
        J_eq=J, V_oc=cfg["bateria"]["V_nominal"], R_int=cfg["bateria"]["R_interna"],
        I_log=cfg["bateria"]["I_logica"], I_fan=(cfg["succion"]["I_media"] if succ else 0.0),
        sx=sx, sy=sy, mancha=op["radio_mancha"], ruido=op["ruido"], umbral=op["umbral"],
        t_lectura=t_lect, T_ctrl=max(cfg["control"]["T_min"], t_lect),
        t_perdida=cfg["control"]["t_perdida"], I_ocp=cfg["conductor"]["I_ocp_min"],
        giro_ruido=cfg["giroscopio"]["ruido"], giro_sesgo=cfg["giroscopio"]["sesgo"],
        ancho_linea=cfg["reglamento"]["ancho_linea"],
        cpr_rueda=float(cfg["motores"][arq["motor"]].get("cpr_motor", 0) * mot.G), prm=prm,
    )
    return replace(c, **cambios) if cambios else c

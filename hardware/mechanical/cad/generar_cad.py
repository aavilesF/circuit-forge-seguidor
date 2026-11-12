#!/usr/bin/env python3
"""CAD mecánico definitivo del Speed Follower (CadQuery), generado de config/robot_maestro.yaml vía
hardware/geometria.py. Marco del robot en mm: x adelante desde el eje de ruedas, y izquierda, z arriba desde el piso.

Salidas (hardware/mechanical/):
  step/  piezas fabricadas (STEP) y ensamble completo robot_completo.step
  stl/   piezas a imprimir (STL)
  planos/ dibujos acotados de las piezas fabricadas (PNG/SVG)
  render/ vistas del robot completo
  propiedades_masa.json, verificacion_mecanica.json
Piezas compradas sin modelo oficial en el entorno (motor, encoder, llanta, batería, bola): modelos SIMPLIFICADOS con
las medidas de su ficha, marcados "APROX" en el nombre. La PCBA viene del STEP exportado por KiCad 9."""
from __future__ import annotations

import json
import math
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vistas  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
MEC = os.path.abspath(os.path.join(AQUI, ".."))
RAIZ = os.path.abspath(os.path.join(MEC, "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "hardware"))
import geometria as GEO  # noqa: E402

G = GEO.cargar()
M = G.m
PCBA_STEP = os.path.join(RAIZ, "hardware", "electronics", "fabricacion", "speed_follower_pcba.step")

# ------------------------------------------------------------------ materiales y masas de piezas compradas [F]
DENS_PA12 = 1.01e-3          # g/mm³ (HP 3D High Reusability PA 12, MJF)
MASAS = {  # g
    "motor": 9.5, "encoder": 0.7, "llanta": 3.12, "bateria": 28.4, "bola": 1.05,
    "tornillo_M2x12": 0.40, "tornillo_M2x8": 0.28, "tuerca_M2": 0.11, "cable_4765": 1.0, "dual_lock": 0.6,
}


def caja(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


# ================================================================== piezas fabricadas (PA12)
def soporte_base(lado):
    """Base del soporte de motor: bloque entre la PCB y el motor, 4 agujeros M2 pasados."""
    y0, y1 = G.y_motor_fin, G.y_reductora
    s = 1 if lado > 0 else -1
    b = caja(-12.0, 12.0, min(s * y0, s * y1), max(s * y0, s * y1), G.z_pcb_sup, G.z_motor_inf)
    for x, ya in M["agujeros_soporte"]:
        b = b.cut(cq.Workplane("XY").circle(1.15).extrude(20).translate((x, s * ya, 0)))
    # rebaje de 0.3 mm para asentar el motor (12.2 de ancho) y evitar que gire
    b = b.cut(caja(-6.1, 6.1, min(s * y0, s * y1), max(s * y0, s * y1), G.z_motor_inf - 0.3, G.z_motor_inf + 1))
    return b


def soporte_tapa(lado):
    """Tapa en U sobre el motor con pestañas atornilladas a la base; su cara superior sostiene la batería."""
    y0, y1 = G.y_motor_fin + 1.4, G.y_reductora - 0.6
    s = 1 if lado > 0 else -1
    ya, yb = min(s * y0, s * y1), max(s * y0, s * y1)
    zi, zs = G.z_motor_inf, G.z_motor_sup
    exterior = caja(-7.6, 7.6, ya, yb, zi, zs + 1.6)
    interior = caja(-6.1, 6.1, ya - 1, yb + 1, zi - 1, zs + 0.1)
    pestanas = caja(-12.0, 12.0, ya, yb, zi, zi + 2.0)
    t = exterior.union(pestanas).cut(interior)
    for x, yy in M["agujeros_soporte"]:
        t = t.cut(cq.Workplane("XY").circle(1.15).extrude(40).translate((x, s * yy, 0)))
    return t


def rueda_loca_carcasa():
    """Carcasa de la rueda loca (bola de 1/4 in): debajo de la PCB, retiene la bola con un labio."""
    x0 = G.x_apoyo
    r_bola = M["bola_diametro"] / 2
    z0 = 1.6                                       # 1.6 mm de la bola sobresalen al piso
    h = G.z_pcb_inf - z0
    c = cq.Workplane("XY").slot2D(16.0, 9.0, 90).extrude(h).translate((x0, 0, z0))
    c = c.cut(cq.Workplane("XY").sphere(r_bola + 0.1).translate((x0, 0, r_bola)))
    for x, y in G.agujeros_rueda_loca_mm():
        c = c.cut(cq.Workplane("XY").circle(1.15).extrude(10).translate((x, y, 0)))
        c = c.cut(cq.Workplane("XY").circle(2.0).extrude(1.35).translate((x, y, z0 - 0.05)))   # caja de la cabeza M2
    return c


def rueda_loca_tapa():
    x0 = G.x_apoyo
    r_bola = M["bola_diametro"] / 2
    t = cq.Workplane("XY").slot2D(16.0, 8.0, 90).extrude(1.2).translate((x0, 0, G.z_pcb_sup))
    t = t.cut(cq.Workplane("XY").sphere(r_bola + 0.15).translate((x0, 0, r_bola)))
    for x, y in G.agujeros_rueda_loca_mm():
        t = t.cut(cq.Workplane("XY").circle(1.15).extrude(10).translate((x, y, 0)))
    return t


# ================================================================== piezas compradas (modelos simplificados)
def motor_aprox(lado):
    """Pololu #3048 (HPCB 12 V 10:1, eje extendido) + encoder #4760: medidas del diagrama 0J949 y de la ficha."""
    s = 1 if lado > 0 else -1
    yr, ym, ye = G.y_reductora, G.y_reductora - M["largo_reductora"], G.y_motor_fin
    zc = G.z_eje

    def tramo(a, b):
        return min(s * a, s * b), max(s * a, s * b)
    a, b = tramo(ym, yr)
    reductora = caja(-6, 6, a, b, zc - 5, zc + 5)
    a, b = tramo(ye, ym)
    lata = cq.Workplane("XZ").circle(6.0).extrude(-(b - a)).translate((0, a, zc)).intersect(caja(-7, 7, a, b, zc - 5, zc + 5))
    eje = cq.Workplane("XZ").circle(1.5).extrude(-9.0).translate((0, min(s * yr, s * (yr + 9.0)), zc))
    buje = cq.Workplane("XZ").circle(2.0).extrude(-1.0).translate((0, min(s * yr, s * (yr + 1.0)), zc))
    # tarjeta del encoder (#4760): sobresale 2.8 mm de la sección de 10 mm, hacia ABAJO; ≈ 5 mm detrás de la tapa
    ancho, alto = M["encoder_tarjeta"]
    e0, e1 = tramo(G.y_encoder_fin, G.y_encoder_fin + 1.0)
    tarjeta = caja(-ancho / 2, ancho / 2, e0, e1, zc + 5 - alto, zc + 5)
    d0, d1 = tramo(G.y_encoder_fin + 1.0, ye)
    disco = cq.Workplane("XZ").circle(3.0).extrude(-(d1 - d0)).translate((0, d0, zc))
    c0, c1 = tramo(G.y_encoder_fin - 4.4, G.y_encoder_fin)
    conector = caja(-3.0, 3.0, c0, c1, zc + 5 - alto + 0.3, zc + 5 - alto + 3.3)   # JST SH de entrada superior
    return reductora.union(lata).union(eje).union(buje).union(tarjeta).union(disco).union(conector)


def llanta_aprox(lado):
    """Pololu #1087: 32 × 7 mm, llanta de silicón; cara exterior al ras del extremo del eje."""
    s = 1 if lado > 0 else -1
    y_ext = G.y_reductora + 9.0
    y_int = y_ext - G.ancho_llanta
    a, b = min(s * y_int, s * y_ext), max(s * y_int, s * y_ext)
    llanta = cq.Workplane("XZ").circle(G.r_rueda).circle(G.r_rueda - 2.0).extrude(-(b - a)).translate((0, a, G.z_eje))
    rin = cq.Workplane("XZ").circle(G.r_rueda - 2.0).circle(2.5).extrude(-(b - a) + 1.0).translate((0, a + 0.5, G.z_eje))
    maza = cq.Workplane("XZ").circle(2.5).circle(1.5).extrude(-(b - a)).translate((0, a, G.z_eje))
    return llanta.union(rin).union(maza)


def bateria_aprox():
    """Tattu TA-75C-450-2S1P-L-XT30: 61 × 16 × 15 mm sobre las tapas de los soportes (con Dual Lock de 1.6 mm)."""
    bx, by, bz = M["bateria_dim"]
    z0 = G.z_motor_sup + 1.6 + 1.6
    return caja(-bx / 2, bx / 2, -by / 2, by / 2, z0, z0 + bz)


def bola():
    r = M["bola_diametro"] / 2
    return cq.Workplane("XY").sphere(r).translate((G.x_apoyo, 0, r))


def tornillo(x, y, largo, desde_abajo=True, z_base=None):
    """M2 de cabeza de botón (Ø3.5 × 1.1 mm). desde_abajo: la cabeza queda bajo z_base y el vástago sube;
    si no, la cabeza queda sobre z_base y el vástago baja."""
    zb = z_base if z_base is not None else G.z_pcb_inf
    if desde_abajo:
        cabeza = cq.Workplane("XY").circle(1.75).extrude(1.1).translate((x, y, zb - 1.1))
        vastago = cq.Workplane("XY").circle(1.0).extrude(largo).translate((x, y, zb))
    else:
        cabeza = cq.Workplane("XY").circle(1.75).extrude(1.1).translate((x, y, zb))
        vastago = cq.Workplane("XY").circle(1.0).extrude(largo).translate((x, y, zb - largo))
    return cabeza.union(vastago)


# ================================================================== ensamble y verificaciones
def pcba():
    """PCBA exportada por KiCad 9 (placa + componentes con sus modelos 3D), con colores. Devuelve
    (compuesto para verificaciones, lista de (nombre, forma, color) para las vistas)."""
    if not os.path.exists(PCBA_STEP):
        raise SystemExit(f"falta {PCBA_STEP}: exportar primero la PCBA (hardware/electronics/generar_fabricacion.sh)")
    asm = cq.Assembly.importStep(PCBA_STEP)
    mover = cq.Location(cq.Vector(0, 0, G.z_pcb_inf))
    piezas = []
    for forma, nombre, loc, color in asm:
        f = forma.moved(mover * loc)
        rgb = color.toTuple()[:3] if color is not None else (0.6, 0.6, 0.6)
        piezas.append((nombre, f, rgb))
    comp = cq.Compound.makeCompound([f for _, f, _ in piezas])
    return cq.Workplane("XY").add(comp), piezas


def construir():
    fabricadas = {
        "soporte_motor_base_izq": soporte_base(+1), "soporte_motor_base_der": soporte_base(-1),
        "soporte_motor_tapa_izq": soporte_tapa(+1), "soporte_motor_tapa_der": soporte_tapa(-1),
        "rueda_loca_carcasa": rueda_loca_carcasa(), "rueda_loca_tapa": rueda_loca_tapa(),
    }
    compradas = {
        "APROX_motor_pololu3048_encoder4760_izq": motor_aprox(+1), "APROX_motor_pololu3048_encoder4760_der": motor_aprox(-1),
        "APROX_llanta_pololu1087_izq": llanta_aprox(+1), "APROX_llanta_pololu1087_der": llanta_aprox(-1),
        "APROX_bateria_tattu450_2s": bateria_aprox(), "APROX_bola_6.35mm": bola(),
    }
    torn = {}
    for i, (x, y) in enumerate(G.agujeros_soportes_mm()):
        torn[f"tornillo_M2x12_{i + 1}"] = tornillo(x, y, 11.0)
    for j, (x, y) in enumerate(G.agujeros_rueda_loca_mm()):
        # desde abajo, con la cabeza dentro de la caja de la carcasa (nada sobresale bajo la carcasa); tuerca sobre la tapa
        torn[f"tornillo_M2x8_rl{j + 1}"] = tornillo(x, y, 8.0, desde_abajo=True, z_base=1.6 + 1.2)
    return fabricadas, compradas, torn


def cajas_tocan(a, b, holgura=0.01):
    p, q = a.val().BoundingBox(), b.val().BoundingBox()
    return (p.xmin <= q.xmax + holgura and q.xmin <= p.xmax + holgura and p.ymin <= q.ymax + holgura and
            q.ymin <= p.ymax + holgura and p.zmin <= q.zmax + holgura and q.zmin <= p.zmax + holgura)


def volumen(w):
    return sum(s.Volume() for s in w.vals())


def cg_de(w):
    vs = w.vals()
    v = sum(s.Volume() for s in vs)
    c = [0, 0, 0]
    for s in vs:
        cc = s.Center()
        c[0] += cc.x * s.Volume(); c[1] += cc.y * s.Volume(); c[2] += cc.z * s.Volume()
    return [ci / v for ci in c]


def main():
    os.makedirs(os.path.join(MEC, "step"), exist_ok=True)
    os.makedirs(os.path.join(MEC, "stl"), exist_ok=True)
    fab, comp, torn = construir()
    for nombre, w in fab.items():
        cq.exporters.export(w, os.path.join(MEC, "step", nombre + ".step"))
        cq.exporters.export(w, os.path.join(MEC, "stl", nombre + ".stl"), tolerance=0.02, angularTolerance=0.1)
    placa, piezas_pcba = pcba()
    # ---------------------------------------------------------------- ensamble
    asm = cq.Assembly(name="speed_follower")
    asm.add(placa, name="PCBA", color=cq.Color(0.10, 0.35, 0.15))
    colores = {"soporte": cq.Color(0.85, 0.85, 0.85), "rueda_loca": cq.Color(0.85, 0.85, 0.85)}
    for n, w in fab.items():
        asm.add(w, name=n, color=colores["soporte" if n.startswith("soporte") else "rueda_loca"])
    for n, w in comp.items():
        col = cq.Color(0.6, 0.6, 0.62) if "motor" in n else cq.Color(0.08, 0.08, 0.08) if "llanta" in n else \
            cq.Color(0.15, 0.25, 0.7) if "bateria" in n else cq.Color(0.75, 0.75, 0.78)
        asm.add(w, name=n, color=col)
    for n, w in torn.items():
        asm.add(w, name=n, color=cq.Color(0.5, 0.5, 0.5))
    asm.export(os.path.join(MEC, "step", "robot_completo.step"))
    # ---------------------------------------------------------------- verificaciones
    sol = {**fab, **comp}
    reporte = dict(interferencias=[], caja={}, masa={}, accesibilidad=[])
    pares = [("soporte_motor_base_izq", "APROX_motor_pololu3048_encoder4760_izq"),
             ("soporte_motor_tapa_izq", "APROX_motor_pololu3048_encoder4760_izq"),
             ("soporte_motor_base_der", "APROX_motor_pololu3048_encoder4760_der"),
             ("soporte_motor_tapa_der", "APROX_motor_pololu3048_encoder4760_der"),
             ("APROX_bateria_tattu450_2s", "soporte_motor_tapa_izq"), ("APROX_bateria_tattu450_2s", "soporte_motor_tapa_der"),
             ("APROX_bateria_tattu450_2s", "APROX_motor_pololu3048_encoder4760_izq"),
             ("APROX_bateria_tattu450_2s", "APROX_motor_pololu3048_encoder4760_der"),
             ("APROX_motor_pololu3048_encoder4760_izq", "APROX_motor_pololu3048_encoder4760_der"),
             ("APROX_llanta_pololu1087_izq", "soporte_motor_base_izq"), ("APROX_llanta_pololu1087_der", "soporte_motor_base_der"),
             ("rueda_loca_carcasa", "APROX_bola_6.35mm"), ("rueda_loca_tapa", "APROX_bola_6.35mm")]
    for a, b in pares:
        v = volumen(sol[a].intersect(sol[b])) if cajas_tocan(sol[a], sol[b]) else 0.0
        reporte["interferencias"].append(dict(a=a, b=b, volumen_mm3=round(v, 3), ok=v < 0.01))
    # PCBA contra piezas mecánicas (cuerpo de componentes y placa)
    for n in ("APROX_motor_pololu3048_encoder4760_izq", "APROX_motor_pololu3048_encoder4760_der",
              "APROX_llanta_pololu1087_izq", "APROX_llanta_pololu1087_der", "APROX_bateria_tattu450_2s",
              "soporte_motor_base_izq", "soporte_motor_base_der", "soporte_motor_tapa_izq", "soporte_motor_tapa_der",
              "APROX_bola_6.35mm", "rueda_loca_carcasa", "rueda_loca_tapa"):
        v = volumen(placa.intersect(sol[n]))
        reporte["interferencias"].append(dict(a="PCBA", b=n, volumen_mm3=round(v, 3), ok=v < 0.05))
    # tornillería contra la PCBA (componentes de la cara inferior y agujeros) y contra las piezas vecinas
    for n, w in torn.items():
        v = volumen(placa.intersect(w))
        reporte["interferencias"].append(dict(a="PCBA", b=n, volumen_mm3=round(v, 3), ok=v < 0.05))
        for m_ in ("APROX_bola_6.35mm", "APROX_motor_pololu3048_encoder4760_izq", "APROX_motor_pololu3048_encoder4760_der"):
            if cajas_tocan(w, sol[m_]):
                v = volumen(w.intersect(sol[m_]))
                reporte["interferencias"].append(dict(a=n, b=m_, volumen_mm3=round(v, 3), ok=v < 0.01))
    bbs = [placa.val().BoundingBox()] + [w.val().BoundingBox() for w in sol.values()]
    xmin = min(b.xmin for b in bbs); xmax = max(b.xmax for b in bbs)
    ymin = min(b.ymin for b in bbs); ymax = max(b.ymax for b in bbs)
    zmin = min(b.zmin for b in bbs); zmax = max(b.zmax for b in bbs)
    reporte["caja"] = dict(largo_x=round(xmax - xmin, 2), ancho_y=round(ymax - ymin, 2), alto_z=round(zmax - zmin, 2),
                           z_min=round(zmin, 3), cumple_200x100=(xmax - xmin) <= 200 and (ymax - ymin) <= 100)
    # ---------------------------------------------------------------- masa y CG
    partes = []
    for n, w in fab.items():
        partes.append((n, volumen(w) * DENS_PA12, cg_de(w)))
    for lado, s in (("izq", 1), ("der", -1)):
        partes.append((f"motor+encoder_{lado}", MASAS["motor"] + MASAS["encoder"], cg_de(comp[f"APROX_motor_pololu3048_encoder4760_{lado}"])))
        partes.append((f"llanta_{lado}", MASAS["llanta"], cg_de(comp[f"APROX_llanta_pololu1087_{lado}"])))
    partes.append(("bateria", MASAS["bateria"], cg_de(comp["APROX_bateria_tattu450_2s"])))
    partes.append(("bola", MASAS["bola"], cg_de(comp["APROX_bola_6.35mm"])))
    for n, w in torn.items():
        partes.append((n, MASAS["tornillo_M2x12"] + MASAS["tuerca_M2"] if "x12" in n else MASAS["tornillo_M2x8"] + MASAS["tuerca_M2"], cg_de(w)))
    partes.append(("cables_encoder (2 × #4765)", 2 * MASAS["cable_4765"], [10.0, 0.0, 12.0]))
    partes.append(("dual_lock (2 piezas)", 2 * MASAS["dual_lock"], [0.0, 0.0, G.z_motor_sup + 2.4]))
    # PCB desnuda y componentes de la PCBA: desde la geometría (área × densidad) y la BOM de ensamblaje
    area = G.area_pcb_mm2() - math.pi * 3.2 ** 2
    cx, cy = G.centroide_pcb_mm()
    m_pcb = area / 100.0 * 0.39
    partes.append(("PCB FR-4 4 capas 1.6 mm", m_pcb, [cx, cy, G.z_pcb_inf + G.t_pcb / 2]))
    m_comp_json = os.path.join(RAIZ, "hardware", "electronics", "verificacion", "masa_componentes.json")
    if os.path.exists(m_comp_json):
        mc = json.load(open(m_comp_json))
        partes.append(("componentes de la PCBA", mc["masa_g"], [mc["x"], mc["y"], mc["z"] + G.z_pcb_inf]))
    m = sum(p[1] for p in partes)
    cgx = sum(p[1] * p[2][0] for p in partes) / m
    cgy = sum(p[1] * p[2][1] for p in partes) / m
    cgz = sum(p[1] * p[2][2] for p in partes) / m
    iz = sum(p[1] * ((p[2][0] - cgx) ** 2 + (p[2][1] - cgy) ** 2) for p in partes) * 1e-9   # kg·m² (puntual)
    reporte["masa"] = dict(total_g=round(m, 1), cg_mm=[round(cgx, 2), round(cgy, 2), round(cgz, 2)], Iz_puntual_kgm2=iz,
                           partes=[dict(nombre=p[0], masa_g=round(p[1], 2), cg_mm=[round(v, 2) for v in p[2]]) for p in partes])
    # ---------------------------------------------------------------- categorías del YAML (componentes) desde el CAD
    def categoria(n):
        for pref, cat in (("motor+encoder", "motores"), ("llanta", "llantas"), ("bateria", "bateria"), ("PCB FR-4", "pcb"),
                          ("componentes de la PCBA", "electronica"), ("soporte", "impresos"), ("rueda_loca", "rueda_loca"),
                          ("bola", "rueda_loca"), ("tornillo", "tornilleria"), ("cables", "cables"), ("dual_lock", "cables")):
            if n.startswith(pref):
                return cat
        raise ValueError(n)
    cats = {}
    for n, mg, c in partes:
        d = cats.setdefault(categoria(n), dict(m=0.0, x=0.0, y=0.0, z=0.0))
        d["m"] += mg; d["x"] += mg * c[0]; d["y"] += mg * abs(c[1]); d["z"] += mg * c[2]
    reporte["masa"]["categorias_yaml"] = {k: dict(masa_kg=round(d["m"] / 1000, 5), x_m=round(d["x"] / d["m"] / 1000, 4),
                                                  y_abs_m=round(d["y"] / d["m"] / 1000, 4), z_m=round(d["z"] / d["m"] / 1000, 4))
                                          for k, d in cats.items()}
    # ---------------------------------------------------------------- alturas sobre el piso (R11)
    alturas = []
    for n, w in {**sol, **torn}.items():
        alturas.append(dict(pieza=n, z_min_mm=round(w.val().BoundingBox().zmin, 3)))
    for nombre, f, _ in piezas_pcba:
        pass
    reporte["alturas"] = dict(z_min_pcba_mm=round(placa.val().BoundingBox().zmin, 3), piezas=alturas,
                              criterio="partes rígidas a ≥ 2 mm del piso salvo llantas, bola y la carcasa de la bola")
    # ---------------------------------------------------------------- accesibilidad (posiciones reales de la PCB)
    plan = json.load(open(os.path.join(RAIZ, "hardware", "electronics", "generador", "plan_pcb.json")))
    pos = {p["ref"]: (p["X"] - plan["X0"], plan["Y0"] - p["Y"]) for p in plan["partes"]}
    bx, by, _ = M["bateria_dim"]
    tapados = [(-bx / 2 - 2, bx / 2 + 2, -by / 2 - 2, by / 2 + 2, "batería")]
    for sgn in (1, -1):
        tapados.append((-14.0, 14.0, min(sgn * G.y_motor_fin, sgn * (G.y_reductora + 9)) - 2,
                        max(sgn * G.y_motor_fin, sgn * (G.y_reductora + 9)) + 2, "motor/soporte"))
    acc = []
    for ref, uso in (("SW2", "botón START"), ("SW3", "botón CAL"), ("SW4", "botón RESET"), ("J4", "conector STDC14 (programación)"),
                     ("J1", "XT30 de la batería"), ("SW1", "interruptor ON/OFF"), ("D3", "LED OK"), ("D4", "LED ERR"), ("D2", "LED 3V3")):
        x, y = pos[ref]
        bloq = [t[4] for t in tapados if t[0] <= x <= t[1] and t[2] <= y <= t[3]]
        acc.append(dict(ref=ref, uso=uso, x_mm=round(x, 1), y_mm=round(y, 1), cara="superior", libre=not bloq, tapado_por=bloq))
    acc.append(dict(ref="bola", uso="cambio de la bola: 2 tuercas M2 sobre la tapa (cara superior)", x_mm=G.x_apoyo, y_mm=0.0,
                    cara="superior", libre=True, tapado_por=[]))
    reporte["accesibilidad"] = acc
    json.dump(reporte, open(os.path.join(MEC, "verificacion_mecanica.json"), "w"), indent=1, ensure_ascii=False)
    json.dump(reporte["masa"], open(os.path.join(MEC, "propiedades_masa.json"), "w"), indent=1, ensure_ascii=False)
    malas = [i for i in reporte["interferencias"] if not i["ok"]]
    print(f"masa {m:.1f} g, CG ({cgx:.1f}, {cgy:.1f}, {cgz:.1f}) mm; caja {reporte['caja']}; interferencias: {len(malas)}")
    for i in malas:
        print("  INTERFERENCIA", i)
    # ---------------------------------------------------------------- vistas y planos
    piezas_vista = [(n, f, c) for n, f, c in piezas_pcba]
    for n, w in fab.items():
        piezas_vista.append((n, w.val(), (0.82, 0.82, 0.80)))
    for n, w in comp.items():
        col = (0.62, 0.62, 0.64) if "motor" in n else (0.10, 0.10, 0.10) if "llanta" in n else \
            (0.18, 0.30, 0.72) if "bateria" in n else (0.80, 0.80, 0.83)
        piezas_vista.append((n, w.val(), col))
    for n, w in torn.items():
        piezas_vista.append((n, w.val(), (0.45, 0.45, 0.47)))
    vistas.renders(piezas_vista, os.path.join(MEC, "render"))
    material = "HP 3D High Reusability PA 12 (MJF), 1.01 g/cm³"
    for n, w in fab.items():
        notas = ["Agujeros M2 pasados Ø2.30 (repasar con broca de 2.3 mm). Tolerancia general ±0.2 mm (MJF)."]
        if "rueda_loca_carcasa" in n:
            notas.append("Caja Ø4.0 × 1.3 mm desde la cara inferior para la cabeza del tornillo M2×8 (queda al ras).")
        vistas.plano_pieza(n, w.val(), os.path.join(MEC, "planos"), material, notas)
    # conjunto: vistas superior y lateral con cotas generales
    contorno = G.contorno_pcb()[0] + [G.contorno_pcb()[0][0]]
    lin_sup = [([p[0] for p in contorno], [p[1] for p in contorno], "g")]
    lin_lat = []
    for n, w in {**fab, **comp}.items():
        col = "0.3" if n.startswith("APROX") else "k"
        for xs, ys in vistas._aristas(w.val(), 0, 1):
            lin_sup.append((xs, ys, col))
        for xs, ys in vistas._aristas(w.val(), 0, 2):
            lin_lat.append((xs, ys, col))
    lin_lat.append(([contorno[0][0], max(p[0] for p in contorno)] * 1, [G.z_pcb_inf, G.z_pcb_inf], "g"))
    lin_lat.append(([min(p[0] for p in contorno), max(p[0] for p in contorno)], [G.z_pcb_sup, G.z_pcb_sup], "g"))
    lin_lat.append(([-30, 130], [0, 0], "0.5"))
    c = reporte["caja"]
    cotas = {"Vista superior": [((xmin, ymin), (xmax, ymin), -6, f"largo {c['largo_x']:.1f}", False),
                                ((xmax, ymin), (xmax, ymax), 6, f"ancho {c['ancho_y']:.1f}", True),
                                ((0, 0), (G.x_apoyo, 0), -3, f"eje-bola {G.x_apoyo:.0f}", False)],
             "Vista lateral": [((xmin, zmin), (xmax, zmin), -4, f"{c['largo_x']:.1f}", False),
                               ((xmax, 0), (xmax, zmax), 5, f"alto {zmax:.1f}", True)]}
    vistas.plano_conjunto({"Vista superior": lin_sup, "Vista lateral": lin_lat}, cotas, os.path.join(MEC, "planos"),
                          titulo=f"Speed Follower — conjunto (masa CAD {m:.1f} g, CG x={cgx:.1f} z={cgz:.1f} mm)")
    return reporte


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""V2 · Constructor de PCB con la API de pcbnew (KiCad 9). Se ejecuta con el Python de KiCad (chroot o KiCad 9 instalado):
  python3 pcb.py construir <plan.json>   -> kicad/<proy>/<proy>.kicad_pcb (huellas, redes, contorno, planos) + <proy>.dsn
  python3 pcb.py importar <plan.json>    -> carga la placa, importa <proy>.ses (Freerouting) y la guarda
  python3 pcb.py pads <plan.json>        -> verificacion/<proy>/pads_pcb.json (red de cada pad, para la conectividad)
Sin dependencias fuera de pcbnew y la biblioteca estándar (el Python del chroot no tiene PyYAML)."""
import json
import math
import os
import sys

import pcbnew as K

AQUI = os.path.dirname(os.path.abspath(__file__))
V2E = os.path.abspath(os.path.join(AQUI, ".."))
SHARE = os.environ.get("KICAD_SHARE", "/usr/share/kicad")
K.Y0_ROBOT = 100.0      # KiCad Y = 100 − y del robot (comun.Y0)
MM = K.FromMM


def V(x, y):
    return K.VECTOR2I(MM(x), MM(y))


def rutas(plan):
    kdir = os.path.join(V2E, "kicad", plan["proy"])
    vdir = os.path.join(V2E, "verificacion", plan["proy"])
    os.makedirs(vdir, exist_ok=True)
    return kdir, vdir, os.path.join(kdir, plan["proy"] + ".kicad_pcb")


def reglas(b, plan):
    ds = b.GetDesignSettings()
    ds.SetBoardThickness(MM(plan["espesor"]))
    ds.m_TrackMinWidth = MM(0.15)
    ds.m_MinClearance = MM(0.127)          # mínimo de JLCPCB (2 capas); las clases piden 0.15-0.2
    ds.m_ViasMinSize = MM(0.5)
    ds.m_MinThroughDrill = MM(0.3)
    ds.m_CopperEdgeClearance = MM(0.25)
    ds.m_HoleClearance = MM(0.25)
    ds.m_HoleToHoleMin = MM(0.3)
    ds.m_SilkClearance = MM(0.0)
    ns = ds.m_NetSettings
    for nombre, c in plan["clases"].items():
        if nombre == "Default":
            nc = ns.GetDefaultNetclass()
        else:
            nc = K.NETCLASS(nombre)
            ns.SetNetclass(nombre, nc)
        nc.SetTrackWidth(MM(c["pista"])); nc.SetClearance(MM(c["separacion"]))
        nc.SetViaDiameter(MM(c["via"])); nc.SetViaDrill(MM(c["taladro"]))
        for pat in c["patrones"]:
            ns.SetNetclassPatternAssignment(pat, nombre)
            ns.SetNetclassPatternAssignment("*/" + pat, nombre)


def contorno(b, pts):
    n = len(pts)
    for i in range(n):
        s = K.PCB_SHAPE(b); s.SetShape(K.SHAPE_T_SEGMENT); s.SetLayer(K.Edge_Cuts); s.SetWidth(MM(0.1))
        s.SetStart(V(*pts[i])); s.SetEnd(V(*pts[(i + 1) % n])); b.Add(s)


def red(b, nombre, cache):
    if nombre not in cache:
        n = K.NETINFO_ITEM(b, nombre)
        b.Add(n)
        cache[nombre] = n
    return cache[nombre]


def campo(fp, nombre, valor):
    f = K.PCB_FIELD(fp, fp.GetNextFieldId() if hasattr(fp, "GetNextFieldId") else fp.GetFieldCount(), nombre)
    f.SetText(valor); f.SetVisible(False); f.SetLayer(K.F_Fab)
    fp.AddField(f)


def huellas(b, plan, nets):
    kdir = rutas(plan)[0]
    for p in plan["partes"]:
        ruta_lib = (os.path.join(kdir, p["lib"] + ".pretty") if p["lib"].startswith("circuitforge")
                    else os.path.join(SHARE, "footprints", p["lib"] + ".pretty"))
        fp = K.FootprintLoad(ruta_lib, p["fp"])
        if fp is None:
            raise RuntimeError("no se encontró %s:%s" % (p["lib"], p["fp"]))
        fp.SetParent(b)
        fp.SetReference(p["ref"]); fp.SetValue(p["valor"])
        fp.SetFPID(K.LIB_ID(p["lib"], p["fp"]))
        try:
            fp.SetSheetname(p["hoja"]); fp.SetSheetfile(p["hoja"] + ".kicad_sch")
        except Exception:
            pass
        campo(fp, "MPN", p["mpn"]); campo(fp, "Fabricante", p["fabricante"])
        if not p["en_bom"]:
            fp.SetExcludedFromBOM(True); fp.SetExcludedFromPosFiles(True)
        b.Add(fp)
        fp.SetPosition(V(p["X"], p["Y"]))
        if p["lado"] == "B":
            fp.Flip(fp.GetPosition(), K.FLIP_DIRECTION_TOP_BOTTOM)
        fp.SetOrientationDegrees(p["rot"])
        for pad in fp.Pads():
            num = pad.GetNumber()
            if num in p["redes"]:
                pad.SetNet(red(b, p["redes"][num], nets))
            elif (p["ref"], num) in plan.get("_nc", {}):
                pad.SetNet(red(b, plan["_nc"][(p["ref"], num)], nets))
        r = fp.Reference()
        if p.get("ref_visible", False):          # serigrafía legible para fabricar: 1.0 mm de alto, trazo 0.15 mm
            r.SetTextSize(K.VECTOR2I(MM(1.0), MM(1.0))); r.SetTextThickness(MM(0.15)); r.SetVisible(True)
        else:
            r.SetTextSize(K.VECTOR2I(MM(0.7), MM(0.7))); r.SetTextThickness(MM(0.1)); r.SetVisible(False)
        if p["ref"] in plan.get("holgura_local", {}):   # LGA de paso 0.5 mm: separación propia entre sus pads (JLCPCB: 0.127 mm)
            fp.SetLocalClearance(MM(plan["holgura_local"][p["ref"]]))


def redes_sin_conexion(plan):
    """Pines sin conexión: KiCad les da en el esquemático la red "unconnected-(REF-PIN-PadN)". Se leen de la lista de
    redes exportada (kicad/<proy>/<proy>.net) para que la paridad esquemático-PCB no tenga diferencias."""
    import re
    ruta = os.path.join(rutas(plan)[0], plan["proy"] + ".net")
    if not os.path.exists(ruta):
        return {}
    texto = open(ruta, encoding="utf-8").read()
    out = {}
    for nombre, cuerpo in re.findall(r'\(net \(code "\d+"\) \(name "(unconnected-[^"]*)"\)(.*?)\)\)\s*(?=\(net|\)\s*\)\s*$)', texto, re.S):
        for ref, pin in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', cuerpo):
            out[(ref, pin)] = nombre
    return out


def textos(b, plan):
    for t in plan.get("textos", []):
        x = K.PCB_TEXT(b)
        x.SetText(t["texto"]); x.SetPosition(V(t["X"], t["Y"]))
        x.SetLayer(K.F_SilkS if t["lado"] == "F" else K.B_SilkS)
        x.SetTextSize(K.VECTOR2I(MM(t["tam"]), MM(t["tam"]))); x.SetTextThickness(MM(max(0.12, t["tam"] * 0.15)))
        if t["lado"] == "B":
            x.SetMirrored(True)
        x.SetTextAngleDegrees(t["rot"])
        b.Add(x)


def zona(b, capa, net, puntos, prioridad=0, solida=False):
    z = K.ZONE(b)
    z.SetLayer(capa); z.SetNet(net); z.SetAssignedPriority(prioridad)
    o = z.Outline(); o.NewOutline()
    for x, y in puntos:
        o.Append(MM(x), MM(y))
    z.SetMinThickness(MM(0.2)); z.SetLocalClearance(MM(0.25))
    z.SetPadConnection(K.ZONE_CONNECTION_FULL if solida else K.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.25)); z.SetThermalReliefSpokeWidth(MM(0.35))
    z.SetIslandRemovalMode(K.ISLAND_REMOVAL_MODE_ALWAYS)
    b.Add(z)


def capas_cobre(b):
    return [c for c in (K.F_Cu, K.In1_Cu, K.In2_Cu, K.B_Cu) if b.IsLayerEnabled(c)]


def capa_id(b, nombre):
    return {"F": K.F_Cu, "B": K.B_Cu}.get(nombre) or b.GetLayerID(nombre)


def prohibidas(b, plan):
    """Áreas de regla: sin cobre (pistas, vías, polígonos) alrededor de los agujeros de montaje, para que la cabeza del
    tornillo no toque cobre; y sin vías bajo el empaque de la chimenea del barómetro de la cámara (una vía abierta fugaría)."""
    def area(x, y, r, sin_cobre):
        z = K.ZONE(b)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(sin_cobre); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
        if hasattr(z, "SetDoNotAllowZoneFills"):
            z.SetDoNotAllowZoneFills(sin_cobre)
        else:
            z.SetDoNotAllowCopperPour(sin_cobre)
        ls = K.LSET()
        for capa in capas_cobre(b):
            ls.AddLayer(capa)
        z.SetLayerSet(ls)
        o = z.Outline(); o.NewOutline()
        for k in range(24):
            ang = 2 * math.pi * k / 24
            o.Append(MM(x + r * math.cos(ang)), MM(y + r * math.sin(ang)))
        b.Add(z)
    for a in plan.get("agujeros", []):
        area(a["X"], a["Y"], a["r"], True)
    for a in plan.get("sin_vias", []):
        area(a["X"], a["Y"], a["r"], False)


def vias_termicas(b, plan, nets):
    """Vías de 0.3 mm (mínimo de JLCPCB para 2 capas) en el pad térmico de los puentes H, al plano de GND inferior."""
    n = 0
    for v in plan.get("vias", []):
        fp = b.FindFootprintByReference(v["ref"])
        pad = fp.FindPadByNumber(v["pad"])
        c, ang = pad.GetPosition(), math.radians(fp.GetOrientationDegrees())
        for dx, dy in v["offsets"]:
            x = MM(dx * math.cos(ang) + dy * math.sin(ang)); y = MM(-dx * math.sin(ang) + dy * math.cos(ang))
            via = K.PCB_VIA(b)
            via.SetPosition(K.VECTOR2I(c.x + x, c.y + y)); via.SetWidth(MM(v["diametro"])); via.SetDrill(MM(v["taladro"]))
            via.SetNet(nets[v["red"]]); via.SetLocked(True)
            b.Add(via); n += 1
    return n


def _dentro(px, py, poli):
    dentro = False
    n = len(poli)
    for i in range(n):
        x1, y1 = poli[i]; x2, y2 = poli[(i + 1) % n]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            dentro = not dentro
    return dentro


def _dist_rect(px, py, r):
    """Distancia de un punto a un rectángulo (x0, y0, x1, y1); 0 si está dentro."""
    dx = max(r[0] - px, 0.0, px - r[2]); dy = max(r[1] - py, 0.0, py - r[3])
    return math.hypot(dx, dy)


def _dist_seg_rect(ax, ay, bx, by, r, n=12):
    return min(_dist_rect(ax + (bx - ax) * k / n, ay + (by - ay) * k / n, r) for k in range(n + 1))


def abanico(b, plan, nets):
    """Vía propia (0.6/0.3 mm) junto a cada pad SMD de las redes con plano interno (GND en In1, +3V3 en In2), unida con
    una pista corta: esas redes no ocupan al enrutador (se quitan del DSN, dsn_sin_red.py) y los planos las conectan.
    Se elige la posición libre más cercana: separación >= 0.25 mm a pads de otras redes, 0.6 mm entre centros de vías,
    0.5 mm al borde, fuera de las áreas prohibidas y de los polígonos de potencia."""
    n_total = 0
    for cfg in plan.get("abanico", []):
        n_total += _abanico_red(b, plan, nets, cfg)
    return n_total


def _abanico_red(b, plan, nets, cfg):
    red, rv, sep, ancho = cfg["red"], cfg["diametro"] / 2, cfg["separacion"], cfg["pista"]
    xs = [p[0] for p in plan["contorno"]]; ys = [p[1] for p in plan["contorno"]]
    borde = (min(xs) + 0.5 + rv, min(ys) + 0.5 + rv, max(xs) - 0.5 - rv, max(ys) - 0.5 - rv)
    prohibido = [(a["X"], a["Y"], a["r"] + rv + 0.1) for a in plan.get("agujeros", []) + plan.get("sin_vias", [])]
    poligonos = [z["puntos"] for z in plan.get("zonas", [])]
    otros, vias, vias_otras, pasillos = [], [], [], []
    for fp in b.GetFootprints():
        fc = fp.GetPosition(); fx, fy = K.ToMM(fc.x), K.ToMM(fc.y)
        for pad in fp.Pads():
            bb = pad.GetBoundingBox()
            rect = (K.ToMM(bb.GetLeft()), K.ToMM(bb.GetTop()), K.ToMM(bb.GetRight()), K.ToMM(bb.GetBottom()))
            if pad.GetNetname() != red:
                otros.append(rect)
                # pasillo de salida de los pads de paso fino de otras redes: 1.3 mm hacia afuera del encapsulado; una vía
                # ahí dejaría al pad sin salida para el enrutador
                w_, h_ = rect[2] - rect[0], rect[3] - rect[1]
                if min(w_, h_) < 0.45 and pad.GetAttribute() == K.PAD_ATTRIB_SMD:
                    cx_, cy_ = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
                    if h_ > w_:      # pad vertical: sale en y
                        pasillos.append((rect[0], rect[1] - 1.3, rect[2], rect[1]) if cy_ < fy else (rect[0], rect[3], rect[2], rect[3] + 1.3))
                    else:
                        pasillos.append((rect[0] - 1.3, rect[1], rect[0], rect[3]) if cx_ < fx else (rect[2], rect[1], rect[2] + 1.3, rect[3]))
    pistas = []                                  # pistas de abanico de otras redes (ya puestas): obstáculos
    for v in b.GetTracks():
        if v.GetClass() == "PCB_VIA":
            vias.append((K.ToMM(v.GetPosition().x), K.ToMM(v.GetPosition().y)))
            if v.GetNetname() != red:
                vias_otras.append(vias[-1])
        elif v.GetNetname() != red:
            pistas.append((K.ToMM(v.GetStart().x), K.ToMM(v.GetStart().y), K.ToMM(v.GetEnd().x), K.ToMM(v.GetEnd().y),
                           K.ToMM(v.GetWidth())))

    def d_punto_seg(x, y, s):
        ax, ay, bx, by = s[0], s[1], s[2], s[3]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        u = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
        return math.hypot(x - ax - u * dx, y - ay - u * dy)

    def libre(x, y, px, py):
        if not (borde[0] <= x <= borde[2] and borde[1] <= y <= borde[3]):
            return False
        if any(math.hypot(x - cx, y - cy) < r for cx, cy, r in prohibido):
            return False
        if any(_dentro(x, y, pg) for pg in poligonos):
            return False
        if any(math.hypot(x - vx, y - vy) < 2 * rv + 0.3 for vx, vy in vias):
            return False
        if any(_dist_rect(x, y, r) < rv + sep for r in otros):
            return False
        if any(_dist_rect(x, y, r) < rv + 0.1 for r in pasillos):
            return False
        return all(d_punto_seg(x, y, s) >= rv + s[4] / 2 + sep for s in pistas)

    n, sin_lugar, propias = 0, [], []
    for fp in b.GetFootprints():
        lado = K.B_Cu if fp.IsFlipped() else K.F_Cu
        for pad in fp.Pads():
            if pad.GetNetname() != red or pad.GetAttribute() != K.PAD_ATTRIB_SMD or pad.GetNumber() in cfg.get("excluir_pads", []):
                continue
            if fp.GetReference() in cfg.get("excluir", []):
                continue
            c = pad.GetPosition(); px, py = K.ToMM(c.x), K.ToMM(c.y)
            # pad dentro de un área sin vías (empaque de la chimenea): la pista sale hasta fuera del área
            dentro_area = any(math.hypot(px - cx, py - cy) < r for cx, cy, r in prohibido)
            destino = cfg.get("unir_a_pad", {}).get(fp.GetReference())
            if destino:           # paso fino con pad térmico (DRV8874): el pin de GND se une al pad térmico, hacia adentro
                ep = fp.FindPadByNumber(destino).GetBoundingBox()
                ex0, ey0, ex1, ey1 = K.ToMM(ep.GetLeft()), K.ToMM(ep.GetTop()), K.ToMM(ep.GetRight()), K.ToMM(ep.GetBottom())
                if ex0 <= px <= ex1:
                    fx, fy = px, (ey0 + 0.3 if py < ey0 else ey1 - 0.3)
                else:
                    fx, fy = (ex0 + 0.3 if px < ex0 else ex1 - 0.3), py
                bbp = pad.GetBoundingBox()
                tr = K.PCB_TRACK(b); tr.SetStart(c); tr.SetEnd(V(fx, fy)); tr.SetLayer(lado); tr.SetNet(nets[red]); tr.SetLocked(True)
                tr.SetWidth(MM(min(ancho, 0.8 * min(K.ToMM(bbp.GetWidth()), K.ToMM(bbp.GetHeight())))))
                b.Add(tr)
                continue
            bb = pad.GetBoundingBox()
            hx, hy = K.ToMM(bb.GetWidth()) / 2, K.ToMM(bb.GetHeight()) / 2
            w = min(ancho, 1.6 * min(hx, hy))          # pads finos (LGA de paso 0.5 mm): pista más angosta
            propio = (px - hx, py - hy, px + hx, py + hy)

            def camino(x, y):
                """Pista del borde del pad a la vía: separación de fabricación (0.16 mm) a los pads de otras redes."""
                k0 = 0.0
                for k in range(1, 41):          # primer punto fuera del pad propio
                    if _dist_rect(px + (x - px) * k / 40, py + (y - py) * k / 40, propio) > 0:
                        k0 = (k - 1) / 40
                        break
                ax, ay = px + (x - px) * k0, py + (y - py) * k0
                if not all(_dist_seg_rect(ax, ay, x, y, r) >= w / 2 + 0.16 for r in otros):
                    return False
                for vx, vy in vias_otras:      # contra vías de otras redes
                    if d_punto_seg(vx, vy, (ax, ay, x, y)) < rv + w / 2 + 0.16:
                        return False
                for s in pistas:              # contra pistas de abanico de otras redes (muestreo cada 1/16)
                    if min(d_punto_seg(px + (x - px) * k / 16, py + (y - py) * k / 16, s) for k in range(17)) < w / 2 + s[4] / 2 + 0.16:
                        return False
                return True
            hecho = False
            # 1) una vía de abanico ya puesta a menos de 1.6 mm con el camino libre: solo la pista
            for vx, vy in sorted(propias, key=lambda q: math.hypot(q[0] - px, q[1] - py)):
                if math.hypot(vx - px, vy - py) > (5.5 if dentro_area else 2.2):
                    break
                if camino(vx, vy):
                    tr = K.PCB_TRACK(b); tr.SetStart(c); tr.SetEnd(V(vx, vy)); tr.SetWidth(MM(w)); tr.SetLayer(lado)
                    tr.SetNet(nets[red]); tr.SetLocked(True); b.Add(tr)
                    hecho = True
                    break
            # 2) vía nueva en la posición libre más cercana
            fino = min(hx, hy) < 0.225           # paso fino (LGA de 0.5 mm): la vía más lejos para que los vecinos salgan
            extras = (0.9, 1.2, 1.5, 2.0, 0.6, 0.45) if fino else (0.35, 0.55, 0.8, 1.1, 1.5, 2.0)
            if dentro_area:
                extras = (3.6, 4.0, 4.4, 4.8, 5.2)
            for extra in extras:
                if hecho:
                    break
                cands = []
                for ang in range(0, 360, 15):
                    a = math.radians(ang)
                    ux, uy = math.cos(a), math.sin(a)
                    s = min(hx / abs(ux) if abs(ux) > 1e-6 else 1e9, hy / abs(uy) if abs(uy) > 1e-6 else 1e9)
                    cands.append((px + ux * (s + rv + extra), py + uy * (s + rv + extra)))
                cands.sort(key=lambda q: math.hypot(q[0] - px, q[1] - py))
                for x, y in cands:
                    if libre(x, y, px, py) and camino(x, y):
                        via = K.PCB_VIA(b); via.SetPosition(V(x, y)); via.SetWidth(MM(2 * rv)); via.SetDrill(MM(cfg["taladro"]))
                        via.SetNet(nets[red]); via.SetLocked(True); b.Add(via)
                        tr = K.PCB_TRACK(b); tr.SetStart(c); tr.SetEnd(V(x, y)); tr.SetWidth(MM(w)); tr.SetLayer(lado)
                        tr.SetNet(nets[red]); tr.SetLocked(True); b.Add(tr)
                        vias.append((x, y)); propias.append((x, y)); n += 1; hecho = True
                        break
            if not hecho:
                sin_lugar.append(f"{fp.GetReference()}.{pad.GetNumber()}")
    if sin_lugar:
        print("  pads de", red, "sin vía propia (los conecta el plano):", " ".join(sin_lugar))
    return n


def pistas_fijas(b, plan):
    """Pistas cortas definidas en el plan (celdas de los puentes H): fijas, Freerouting las respeta y las conserva."""
    n = 0
    for pf in plan.get("pistas_fijas", []):
        ref, num = pf["pad"]
        pad0 = b.FindFootprintByReference(ref).FindPadByNumber(num)
        net, capa = pad0.GetNet(), (K.B_Cu if pf.get("capa") == "B" else K.F_Cu)
        pts = []
        for q in pf["puntos"]:
            if isinstance(q[0], str):            # ("pad", ref, número)
                c = b.FindFootprintByReference(q[1]).FindPadByNumber(q[2]).GetPosition()
                pts.append(c)
            else:
                pts.append(V(q[0], K.Y0_ROBOT - q[1]))
        for a, c in zip(pts[:-1], pts[1:]):
            tr = K.PCB_TRACK(b); tr.SetStart(a); tr.SetEnd(c); tr.SetWidth(MM(pf["ancho"])); tr.SetLayer(capa)
            tr.SetNet(net); tr.SetLocked(True); b.Add(tr); n += 1
    return n


def construir(plan):
    kdir, vdir, salida = rutas(plan)
    b = K.CreateEmptyBoard()
    b.SetCopperLayerCount(plan["capas"])
    for nombre_capa, tipo in plan.get("tipo_capas", {}).items():
        b.SetLayerType(b.GetLayerID(nombre_capa), K.LT_POWER if tipo == "power" else K.LT_SIGNAL)
    reglas(b, plan)
    tb = b.GetTitleBlock()
    tb.SetTitle(plan["titulo"]); tb.SetCompany("Circuit Forge — Robolympics RMX2026"); tb.SetRevision("V2-A")
    tb.SetDate("2026-11-04"); tb.SetComment(0, "Generada por hardware/v2/electronica/generador/pcb.py")
    contorno(b, plan["contorno"])
    nets = {}
    plan["_nc"] = redes_sin_conexion(plan)
    huellas(b, plan, nets)
    textos(b, plan)
    prohibidas(b, plan)
    nt = pistas_fijas(b, plan)
    nv = vias_termicas(b, plan, nets)
    nv += abanico(b, plan, nets)
    ds = b.GetDesignSettings()
    ds.SetAuxOrigin(V(*plan["origen_aux"])); ds.SetGridOrigin(V(*plan["origen_aux"]))
    b.BuildListOfNets()
    K.SaveBoard(salida, b)
    dsn = os.path.join(kdir, plan["proy"] + ".dsn")
    ok = K.ExportSpecctraDSN(b, dsn)
    print("placa construida:", salida, "| DSN:", ok, "| vías fijas:", nv, "| pistas fijas:", nt)


def quitar_colgantes(b):
    """Quita, de forma iterativa, los tramos con un extremo libre y las vías que unen menos de dos elementos (restos
    que Freerouting deja al optimizar)."""
    total = 0
    vistos = set()
    for t in [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]:   # segmentos repetidos (ida y vuelta)
        a, c = (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)
        k = (t.GetLayer(), t.GetNetCode(), min(a, c), max(a, c))
        if k in vistos or a == c:
            b.Delete(t); total += 1
        else:
            vistos.add(k)
    while True:
        tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
        vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
        pads_ = [p for fp in b.GetFootprints() for p in fp.Pads()]

        def toca_via(v, pt):
            return (v.GetPosition() - pt).EuclideanNorm() <= v.GetWidth(K.F_Cu) // 2

        quitar = []
        for t in tracks:
            for pt in (t.GetStart(), t.GetEnd()):
                n = sum(1 for o in tracks if o is not t and o.GetNetCode() == t.GetNetCode() and o.GetLayer() == t.GetLayer()
                        and o.HitTest(pt))
                n += sum(1 for v in vias if v.GetNetCode() == t.GetNetCode() and toca_via(v, pt))
                n += sum(1 for p in pads_ if p.GetNetCode() == t.GetNetCode() and p.IsOnLayer(t.GetLayer()) and p.HitTest(pt))
                if n == 0:
                    quitar.append(t)
                    break
        for v in vias:
            pos = v.GetPosition()
            n = sum(1 for t in tracks if t.GetNetCode() == v.GetNetCode() and (toca_via(v, t.GetStart()) or toca_via(v, t.GetEnd())))
            n += sum(1 for p in pads_ if p.GetNetCode() == v.GetNetCode() and p.HitTest(pos))
            if n < 2 and not v.IsLocked():       # las vías térmicas (fijas) solo tocan su pad y el plano
                quitar.append(v)
        if not quitar:
            break
        for t in quitar:
            b.Delete(t)
        total += len(quitar)
    print("tramos y vías colgantes quitados:", total)


def importar(plan):
    kdir, vdir, salida = rutas(plan)
    b = K.LoadBoard(salida)
    ses = os.path.join(kdir, plan["proy"] + ".ses")
    ok = K.ImportSpecctraSES(b, ses)
    nets = {n.GetNetname(): n for n in b.GetNetsByName().values()} if hasattr(b, "GetNetsByName") else {}
    nets = {}
    for i in range(b.GetNetCount()):
        n = b.FindNet(i)
        if n:
            nets[n.GetNetname()] = n
    for pl in plan.get("planos", []):
        zona(b, capa_id(b, pl["capa"]), nets[pl["red"]], plan["contorno"])
    for zz in plan.get("zonas", []):          # cobre de potencia, por encima del plano de GND
        for capa in zz["capas"]:
            zona(b, capa_id(b, capa), nets[zz["red"]], zz["puntos"], prioridad=zz["prioridad"], solida=True)
    vt = sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.IsLocked())
    if plan.get("vias") and vt == 0:          # si la importación del SES quitó las vías fijas, se vuelven a poner
        print("vías térmicas repuestas:", vias_termicas(b, plan, nets))
    # Freerouting enruta con la separación de ruteo del plan; la regla final del DRC es la de fabricación
    ns = b.GetDesignSettings().m_NetSettings
    for nombre, c in plan["clases"].items():
        nc = ns.GetDefaultNetclass() if nombre == "Default" else ns.GetNetclasses()[nombre]
        nc.SetClearance(MM(c.get("separacion_drc", 0.15)))
    for fp in b.GetFootprints():          # pestañas mecánicas de conectores: conexión sólida al plano
        for pad in fp.Pads():
            if pad.GetNumber() == "MP" or (fp.GetReference(), pad.GetNumber()) in {tuple(x) for x in plan.get("conexion_solida", [])}:
                pad.SetLocalZoneConnection(K.ZONE_CONNECTION_FULL)
    quitar_colgantes(b)
    K.SaveBoard(salida, b)
    pistas = sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_TRACK")
    vias = sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_VIA")
    print("SES importado:", ok, "| pistas", pistas, "| vías", vias)


def pads(plan):
    kdir, vdir, salida = rutas(plan)
    b = K.LoadBoard(salida)
    out = []
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNumber() not in ("", None):
                out.append(dict(ref=fp.GetReference(), pad=pad.GetNumber(), red=pad.GetNetname().split("/")[-1],
                                X=K.ToMM(pad.GetPosition().x), Y=K.ToMM(pad.GetPosition().y), lado="B" if fp.IsFlipped() else "F"))
    json.dump(out, open(os.path.join(vdir, "pads_pcb.json"), "w"), indent=0)
    print("pads:", len(out))


def rellenar(plan):
    """Relleno de zonas en un proceso aparte (cargar desde archivo le da proyecto y ajustes al rellenador)."""
    salida = rutas(plan)[2]
    b = K.LoadBoard(salida)
    zonas = [z for z in b.Zones() if not z.GetIsRuleArea()]
    K.ZONE_FILLER(b).Fill(b.Zones())
    K.SaveBoard(salida, b)
    print("zonas rellenas: %d/%d" % (sum(1 for z in zonas if z.IsFilled()), len(zonas)))


if __name__ == "__main__":
    modo, ruta_plan = sys.argv[1], sys.argv[2]
    plan = json.load(open(ruta_plan))
    {"construir": construir, "importar": importar, "pads": pads, "rellenar": rellenar}[modo](plan)

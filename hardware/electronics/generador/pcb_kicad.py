#!/usr/bin/env python3
"""Construye la PCB con la API de pcbnew (KiCad 9). Se ejecuta con el Python de KiCad:
  python3 pcb_kicad.py construir   -> kicad/speed_follower.kicad_pcb (sin pistas) + geometria_pcb.json
  python3 pcb_kicad.py final       -> igual + pistas/vías de rutas.json + planos + relleno de zonas
Lee plan_pcb.json (pcb_plan.py) y rutas.json (enrutar.py). No depende de numpy."""
import json
import math
import os
import sys

import pcbnew as K

AQUI = os.path.dirname(os.path.abspath(__file__))
EDIR = os.path.abspath(os.path.join(AQUI, ".."))
KDIR = os.path.join(EDIR, "kicad")
VDIR = os.path.join(EDIR, "verificacion")
SHARE = os.environ.get("KICAD_SHARE", "/usr/share/kicad")
MM = K.FromMM


def V(x, y):
    return K.VECTOR2I(MM(x), MM(y))


def capas(b):
    b.SetCopperLayerCount(4)
    b.SetEnabledLayers(b.GetEnabledLayers())


def reglas(b, plan):
    ds = b.GetDesignSettings()
    ds.SetBoardThickness(MM(plan["espesor"]))
    ds.m_TrackMinWidth = MM(0.15)
    ds.m_MinClearance = MM(0.15)
    ds.m_ViasMinSize = MM(0.45)
    ds.m_MinThroughDrill = MM(0.20)     # vías térmicas de 0.2 mm de la huella oficial del DRV8833 (PowerPAD); vías propias 0.25
    ds.m_CopperEdgeClearance = MM(0.3)
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
            ns.SetNetclassPatternAssignment("*/" + pat, nombre)       # redes locales de una hoja: "/Hoja/RED"


def contorno(b, plan):
    pts = plan["contorno"]
    a = plan["arco"]
    ini, fin = tuple(a["inicio"]), tuple(a["fin"])
    # segmentos rectos del contorno + un arco verdadero para el frente
    n = len(pts)
    i_ini = min(range(n), key=lambda i: (pts[i][0] - ini[0]) ** 2 + (pts[i][1] - ini[1]) ** 2)
    i_fin = min(range(n), key=lambda i: (pts[i][0] - fin[0]) ** 2 + (pts[i][1] - fin[1]) ** 2)
    i = i_fin
    while True:                                   # de fin del arco, recorriendo el resto, hasta inicio del arco
        j = (i + 1) % n
        s = K.PCB_SHAPE(b); s.SetShape(K.SHAPE_T_SEGMENT); s.SetLayer(K.Edge_Cuts); s.SetWidth(MM(0.1))
        s.SetStart(V(*pts[i])); s.SetEnd(V(*pts[j])); b.Add(s)
        i = j
        if i == i_ini:
            break
    arc = K.PCB_SHAPE(b); arc.SetShape(K.SHAPE_T_ARC); arc.SetLayer(K.Edge_Cuts); arc.SetWidth(MM(0.1))
    cx, cy = a["centro"]
    mid = (cx + a["r"], cy)
    arc.SetArcGeometry(V(*pts[i_ini]), V(*mid), V(*pts[i_fin]))
    b.Add(arc)
    c = K.PCB_SHAPE(b); c.SetShape(K.SHAPE_T_CIRCLE); c.SetLayer(K.Edge_Cuts); c.SetWidth(MM(0.1))
    bx, by = plan["agujero_bola"]["centro"]
    c.SetCenter(V(bx, by)); c.SetEnd(V(bx + plan["agujero_bola"]["diametro"] / 2, by)); b.Add(c)


NOMBRES_RED = {}            # nombre del diseño -> nombre del esquemático (plan_pcb.json)


def red(b, nombre, cache):
    if nombre not in cache:
        n = K.NETINFO_ITEM(b, NOMBRES_RED.get(nombre, nombre))
        b.Add(n)
        cache[nombre] = n
    return cache[nombre]


def campo(fp, nombre, valor):
    try:
        f = K.PCB_FIELD(fp, fp.GetNextFieldId() if hasattr(fp, "GetNextFieldId") else fp.GetFieldCount(), nombre)
    except Exception:
        f = K.PCB_FIELD(fp, 0, nombre)
    f.SetText(valor); f.SetVisible(False); f.SetLayer(K.F_Fab)
    fp.AddField(f)


def huellas(b, plan, nets):
    for p in plan["partes"]:
        ruta_lib = os.path.join(KDIR, "circuitforge.pretty") if p["lib"] == "circuitforge" else \
            os.path.join(SHARE, "footprints", p["lib"] + ".pretty")
        fp = K.FootprintLoad(ruta_lib, p["fp"])
        if fp is None:
            raise RuntimeError(f"no se encontró {p['lib']}:{p['fp']}")
        fp.SetParent(b)
        fp.SetReference(p["ref"]); fp.SetValue(p["valor"])
        fp.SetFPID(K.LIB_ID(p["lib"], p["fp"]))
        fp.SetPath(K.KIID_PATH(p["ruta"]))
        try:
            fp.SetSheetname(p["hoja"]); fp.SetSheetfile(p["hoja"] + ".kicad_sch")
        except Exception:
            pass
        for kk, vv in p["campos"].items():
            if kk == "Datasheet":
                try:
                    fp.GetField(K.FIELD_T_DATASHEET if hasattr(K, "FIELD_T_DATASHEET") else 3).SetText(vv)
                except Exception:
                    campo(fp, kk, vv)
            else:
                campo(fp, kk, vv)
        if not p["en_bom"]:
            fp.SetExcludedFromBOM(True)
            if p["ref"].startswith("H"):
                fp.SetExcludedFromPosFiles(True)
        b.Add(fp)
        fp.SetPosition(V(p["X"], p["Y"]))
        if p["lado"] == "B":
            fp.Flip(fp.GetPosition(), K.FLIP_DIRECTION_TOP_BOTTOM if hasattr(K, "FLIP_DIRECTION_TOP_BOTTOM") else False)
        fp.SetOrientationDegrees(p["rot"])
        if p.get("modelo3d"):
            nombre = p["modelo3d"].split(":")[1]
            mods = fp.Models()
            mods.clear()
            m = K.FP_3DMODEL(); m.m_Filename = "${KIPRJMOD}/3d/" + nombre + ".step"
            mods.push_back(m)
        if p.get("modelo3d_oficial"):
            mods = fp.Models()
            mods.clear()
            m = K.FP_3DMODEL(); m.m_Filename = "${KICAD9_3DMODEL_DIR}/" + p["modelo3d_oficial"]
            mods.push_back(m)
        for pad in fp.Pads():
            num = pad.GetNumber()
            if num in p["redes"]:
                pad.SetNet(red(b, p["redes"][num], nets))
            elif num == "" or num is None:
                pass
        if p["ref"] == "J4":     # pines de 1.27 mm: el alivio térmico al plano queda con un solo rayo -> conexión sólida
            for pad in fp.Pads():
                pad.SetLocalZoneConnection(K.ZONE_CONNECTION_FULL)
        # Placa densa: las referencias van en la capa de fabricación (planos de ensamblaje, ${REFERENCE} de cada huella
        # oficial) y no en la serigrafía; en la serigrafía quedan los rótulos funcionales (START, CAL, ENC IZQ, S1…).
        r = fp.Reference()
        r.SetTextSize(K.VECTOR2I(MM(0.8), MM(0.8))); r.SetTextThickness(MM(0.12))
        r.SetVisible(False)


def textos(b, plan):
    for t in plan["textos"]:
        x = K.PCB_TEXT(b)
        x.SetText(t["texto"]); x.SetPosition(V(t["X"], t["Y"]))
        x.SetLayer(K.F_SilkS if t["lado"] == "F" else K.B_SilkS)
        x.SetTextSize(K.VECTOR2I(MM(t["tam"]), MM(t["tam"]))); x.SetTextThickness(MM(max(0.12, t["tam"] * 0.15)))
        if t["lado"] == "B":
            x.SetMirrored(True)
        x.SetTextAngleDegrees(t["rot"])
        b.Add(x)


def zona(b, capa, net, puntos, prioridad=0, regla=False, nombre="", agujeros=()):
    z = K.ZONE(b)
    z.SetLayer(capa)
    if net is not None:
        z.SetNet(net)
    o = z.Outline(); o.NewOutline()
    for x, y in puntos:
        o.Append(MM(x), MM(y))
    for cx, cy, r in agujeros:         # huecos (p. ej., los agujeros de tornillo dentro de un área prohibida)
        ih = o.NewHole()
        for k in range(24):
            a = 2 * math.pi * k / 24
            o.Append(MM(cx + r * math.cos(a)), MM(cy + r * math.sin(a)), 0, ih)
    z.SetAssignedPriority(prioridad)
    if regla:
        z.SetIsRuleArea(True)
        z.SetDoNotAllowFootprints(True); z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(False)
        z.SetDoNotAllowPads(False)
        z.SetZoneName(nombre)
    else:
        z.SetMinThickness(MM(0.2)); z.SetLocalClearance(MM(0.25))
        z.SetPadConnection(K.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(MM(0.25)); z.SetThermalReliefSpokeWidth(MM(0.35))
        z.SetIslandRemovalMode(K.ISLAND_REMOVAL_MODE_ALWAYS)
    b.Add(z)
    return z


def exportar_geometria(b, ruta):
    pads, huellas_ = [], []
    for fp in b.GetFootprints():
        try:
            fp.BuildCourtyardCaches()
        except Exception:
            pass
        lado = "B" if fp.IsFlipped() else "F"
        cy = fp.GetCourtyard(K.B_CrtYd if lado == "B" else K.F_CrtYd)
        poly = []
        if cy.OutlineCount():
            ol = cy.Outline(0)
            poly = [(K.ToMM(ol.CPoint(i).x), K.ToMM(ol.CPoint(i).y)) for i in range(ol.PointCount())]
        bb = fp.GetBoundingBox(False)
        huellas_.append(dict(ref=fp.GetReference(), lado=lado, X=K.ToMM(fp.GetPosition().x), Y=K.ToMM(fp.GetPosition().y),
                             rot=fp.GetOrientationDegrees(), cortijo=poly,
                             caja=[K.ToMM(bb.GetLeft()), K.ToMM(bb.GetTop()), K.ToMM(bb.GetRight()), K.ToMM(bb.GetBottom())]))
        for pad in fp.Pads():
            ls = pad.GetLayerSet()
            capas_ = [n for n, l in (("F", K.F_Cu), ("B", K.B_Cu)) if ls.Contains(l)]
            forma = {K.PAD_SHAPE_RECTANGLE if hasattr(K, "PAD_SHAPE_RECTANGLE") else K.PAD_SHAPE_RECT: "rect",
                     K.PAD_SHAPE_ROUNDRECT: "roundrect", K.PAD_SHAPE_CIRCLE: "circle", K.PAD_SHAPE_OVAL: "oval"}.get(
                pad.GetShape(K.F_Cu) if hasattr(pad, "GetShape") else pad.GetShape(), "custom")
            sz = pad.GetSize(K.F_Cu) if pad.GetAttribute() != K.PAD_ATTRIB_SMD or lado == "F" else pad.GetSize(K.B_Cu)
            try:
                sz = pad.GetSize(K.F_Cu)
            except Exception:
                sz = pad.GetSize()
            drill = K.ToMM(pad.GetDrillSize().x) if pad.GetDrillSize().x else 0.0
            radio = 0.0
            if forma == "roundrect":
                try:
                    radio = K.ToMM(pad.GetRoundRectCornerRadius(K.F_Cu))
                except Exception:
                    radio = K.ToMM(pad.GetRoundRectCornerRadius())
            pads.append(dict(ref=fp.GetReference(), pad=pad.GetNumber(), red=pad.GetNetname().split("/")[-1],
                             X=K.ToMM(pad.GetPosition().x), Y=K.ToMM(pad.GetPosition().y),
                             w=K.ToMM(sz.x), h=K.ToMM(sz.y), ang=pad.GetOrientationDegrees(), forma=forma, radio=radio,
                             capas=capas_, taladro=drill,
                             npth=pad.GetAttribute() == K.PAD_ATTRIB_NPTH))
    json.dump(dict(huellas=huellas_, pads=pads), open(ruta, "w"), indent=0)
    # versión reducida para la verificación de conectividad
    json.dump([dict(ref=p["ref"], pad=p["pad"], red=p["red"]) for p in pads if p["pad"] not in ("", None)],
              open(os.path.join(VDIR, "pads_pcb.json"), "w"), indent=0)


def cotas(b, plan):
    """Cotas y geometría de referencia en Dwgs.User (aparecen en los planos de ensamblaje)."""
    X0, Y0 = plan["X0"], plan["Y0"]
    xs = [p[0] for p in plan["contorno"]]; ys = [p[1] for p in plan["contorno"]]
    xmax = X0 + plan["arco"]["r"]

    def dim(a, b_, h, vertical=None):
        d = K.PCB_DIM_ORTHOGONAL(b) if vertical is not None else K.PCB_DIM_ALIGNED(b)
        d.SetLayer(K.Dwgs_User)
        d.SetStart(V(*a)); d.SetEnd(V(*b_)); d.SetHeight(MM(h))
        if vertical is not None:
            d.SetOrientation(K.PCB_DIM_ORTHOGONAL.DIR_VERTICAL if vertical else K.PCB_DIM_ORTHOGONAL.DIR_HORIZONTAL)
        d.SetUnitsMode(K.DIM_UNITS_MODE_MM) if hasattr(d, "SetUnitsMode") else None
        d.SetPrecision(K.DIM_PRECISION_X_X) if hasattr(K, "DIM_PRECISION_X_X") else None
        d.SetLineThickness(MM(0.1)); d.SetTextSize(K.VECTOR2I(MM(1.2), MM(1.2)))
        b.Add(d)
    dim((min(xs), Y0), (xmax, Y0), -54.0, vertical=False)                  # largo total
    dim((X0 + 60, min(ys)), (X0 + 60, max(ys)), -70.0, vertical=True)      # ancho total
    dim((min(xs), Y0), (X0, Y0), 8.0, vertical=False)                      # borde trasero - eje
    dim((X0, Y0), (X0 + plan["agujero_bola"]["centro"][0] - X0, Y0), 12.0, vertical=False)
    for v in plan["partes"]:
        pass
    # arco de sensores R110 y eje de ruedas
    r_s = plan.get("r_sensores", 110.0)
    arc = K.PCB_SHAPE(b); arc.SetShape(K.SHAPE_T_ARC); arc.SetLayer(K.Dwgs_User); arc.SetWidth(MM(0.1))
    import math as _m
    a0 = _m.radians(26.0)
    arc.SetArcGeometry(V(X0 + r_s * _m.cos(a0), Y0 + r_s * _m.sin(a0)), V(X0 + r_s, Y0), V(X0 + r_s * _m.cos(a0), Y0 - r_s * _m.sin(a0)))
    b.Add(arc)
    eje = K.PCB_SHAPE(b); eje.SetShape(K.SHAPE_T_SEGMENT); eje.SetLayer(K.Dwgs_User); eje.SetWidth(MM(0.1))
    eje.SetStart(V(X0, Y0 - 50)); eje.SetEnd(V(X0, Y0 + 50)); b.Add(eje)
    for txt, x, y in [("EJE DE RUEDAS (origen x=0)", X0 + 1, Y0 - 48), (f"ARCO DE SENSORES R{r_s:.0f} (centro en el eje)", X0 + 70, Y0 - 50),
                      ("Cotas en mm. Origen de coordenadas de fabricación: centro del eje de ruedas (100, 100) en KiCad", min(xs), Y0 + 60)]:
        t = K.PCB_TEXT(b); t.SetText(txt); t.SetPosition(V(x, y)); t.SetLayer(K.Dwgs_User)
        t.SetTextSize(K.VECTOR2I(MM(1.2), MM(1.2))); t.SetTextThickness(MM(0.15))
        t.SetHorizJustify(K.GR_TEXT_H_ALIGN_LEFT); b.Add(t)


def rutas(b, nets, ruta):
    if not os.path.exists(ruta):
        return 0, 0
    R = json.load(open(ruta))
    capa = {"F": K.F_Cu, "B": K.B_Cu}
    nt = nv = 0
    for t in R["pistas"]:
        x = K.PCB_TRACK(b)
        x.SetStart(V(t["x1"], t["y1"])); x.SetEnd(V(t["x2"], t["y2"]))
        x.SetWidth(MM(t["w"])); x.SetLayer(capa[t["capa"]]); x.SetNet(nets[t["red"]])
        b.Add(x); nt += 1
    for v in R["vias"]:
        x = K.PCB_VIA(b)
        x.SetPosition(V(v["x"], v["y"])); x.SetViaType(K.VIATYPE_THROUGH)
        x.SetLayerPair(K.F_Cu, K.B_Cu)
        x.SetWidth(MM(v["d"])); x.SetDrill(MM(v["t"])); x.SetNet(nets[v["red"]])
        b.Add(x); nv += 1
    return nt, nv


def principal(modo):
    plan = json.load(open(os.path.join(AQUI, "plan_pcb.json")))
    NOMBRES_RED.update(plan.get("nombres_red", {}))
    b = K.CreateEmptyBoard()
    capas(b)
    reglas(b, plan)
    tb = b.GetTitleBlock()
    tb.SetTitle("Speed Follower — PCB-chasis"); tb.SetCompany("Circuit Forge — Robolympics RMX2026")
    tb.SetRevision("1.0"); tb.SetDate("2026-11-01")
    tb.SetComment(0, "Generada por hardware/electronics/generador (diseno.py -> pcb_plan.py -> pcb_kicad.py)")
    contorno(b, plan)
    nets = {}
    huellas(b, plan, nets)
    textos(b, plan)
    hs = [(p["X"], p["Y"]) for p in plan["partes"] if p["ref"].startswith("H")]
    for i, (x0, y0, x1, y1) in enumerate(plan["zonas_prohibidas"]):
        dentro = [(x, y, 2.7) for x, y in hs if min(x0, x1) <= x <= max(x0, x1) and min(y0, y1) <= y <= max(y0, y1)]
        zona(b, K.F_Cu, None, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], regla=True, nombre=f"soporte_motor_{i}",
             agujeros=dentro)
    b.BuildListOfNets()
    if modo == "construir":
        exportar_geometria(b, os.path.join(AQUI, "geometria_pcb.json"))
    else:
        nt, nv = rutas(b, nets, os.path.join(AQUI, "rutas.json"))
        cotas(b, plan)
        ds = b.GetDesignSettings()
        ds.SetAuxOrigin(V(plan["X0"], plan["Y0"])); ds.SetGridOrigin(V(plan["X0"], plan["Y0"]))
        cont = [tuple(p) for p in plan["contorno"]]
        zona(b, K.In1_Cu, nets["GND"], cont, 0)
        zona(b, K.In2_Cu, nets["+3V3"], cont, 0)
        zona(b, K.F_Cu, nets["GND"], cont, 0)
        zona(b, K.B_Cu, nets["GND"], cont, 0)
        # El relleno de zonas lo hace kicad-cli (drc --refill-zones --save-board): ZONE_FILLER desde Python sin la
        # interfaz gráfica termina en violación de segmento en KiCad 9.0.8.
        exportar_geometria(b, os.path.join(AQUI, "geometria_pcb_final.json"))
        print(f"pistas {nt}, vías {nv}")
    salida = os.path.join(KDIR, "speed_follower.kicad_pcb")
    b.Save(salida) if hasattr(b, "Save") else K.SaveBoard(salida, b)
    K.SaveBoard(salida, b)
    print("guardado", salida)


if __name__ == "__main__":
    principal(sys.argv[1] if len(sys.argv) > 1 else "construir")

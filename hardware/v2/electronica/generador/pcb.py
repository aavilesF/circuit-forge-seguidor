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
    ds.m_MinClearance = MM(0.15)
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
        r = fp.Reference()
        r.SetTextSize(K.VECTOR2I(MM(0.7), MM(0.7))); r.SetTextThickness(MM(0.1))
        r.SetVisible(p.get("ref_visible", False))


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


def zona(b, capa, net, puntos):
    z = K.ZONE(b)
    z.SetLayer(capa); z.SetNet(net)
    o = z.Outline(); o.NewOutline()
    for x, y in puntos:
        o.Append(MM(x), MM(y))
    z.SetMinThickness(MM(0.2)); z.SetLocalClearance(MM(0.25))
    z.SetPadConnection(K.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.25)); z.SetThermalReliefSpokeWidth(MM(0.35))
    z.SetIslandRemovalMode(K.ISLAND_REMOVAL_MODE_ALWAYS)
    b.Add(z)


def construir(plan):
    kdir, vdir, salida = rutas(plan)
    b = K.CreateEmptyBoard()
    b.SetCopperLayerCount(plan["capas"])
    reglas(b, plan)
    tb = b.GetTitleBlock()
    tb.SetTitle(plan["titulo"]); tb.SetCompany("Circuit Forge — Robolympics RMX2026"); tb.SetRevision("V2-A")
    tb.SetDate("2026-11-04"); tb.SetComment(0, "Generada por hardware/v2/electronica/generador/pcb.py")
    contorno(b, plan["contorno"])
    nets = {}
    huellas(b, plan, nets)
    textos(b, plan)
    ds = b.GetDesignSettings()
    ds.SetAuxOrigin(V(*plan["origen_aux"])); ds.SetGridOrigin(V(*plan["origen_aux"]))
    b.BuildListOfNets()
    K.SaveBoard(salida, b)
    dsn = os.path.join(kdir, plan["proy"] + ".dsn")
    ok = K.ExportSpecctraDSN(b, dsn)
    print("placa construida:", salida, "| DSN:", ok)


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
            if n < 2:
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
        zona(b, K.F_Cu if pl["capa"] == "F" else K.B_Cu, nets[pl["red"]], plan["contorno"])
    # Freerouting enruta con la separación de ruteo del plan; la regla final del DRC es la de fabricación
    ns = b.GetDesignSettings().m_NetSettings
    for nombre, c in plan["clases"].items():
        nc = ns.GetDefaultNetclass() if nombre == "Default" else ns.GetNetclasses()[nombre]
        nc.SetClearance(MM(c.get("separacion_drc", 0.15)))
    for fp in b.GetFootprints():          # pestañas mecánicas de conectores: conexión sólida al plano
        for pad in fp.Pads():
            if pad.GetNumber() == "MP":
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

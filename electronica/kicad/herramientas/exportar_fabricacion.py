#!/usr/bin/env python3.12
"""Archivos para fabricar la PCB en casa (planchado / transferencia de tóner + cloruro férrico + taladro).

Uso: python3.12 exportar_fabricacion.py principal|sensores

Genera en <placa>/fabricacion/:
  <placa>_cobre_1a1.pdf      Patrón de cobre (cara inferior, B.Cu) + contorno + marcas de taladro, escala 1:1,
                             listo para imprimir en láser y planchar. Incluye una regla de 50 mm para comprobar la escala.
  <placa>_perforaciones.csv  Una fila por agujero: ID, pieza, pata, X, Y (mm desde la esquina superior izquierda
                             de la placa vista desde los COMPONENTES), diámetro de diseño y broca sugerida.
  <placa>_perforaciones.pdf  Mapa de perforaciones 1:1 (vista desde los componentes) con el ID de cada agujero.
  <placa>_puentes.csv        Pistas de la cara superior (F.Cu): son PUENTES DE ALAMBRE, no se graban.
  LEEME.md                   Resumen: tamaño, número de agujeros por broca, puentes, cómo imprimir.

Orientación (la placa es de UNA cara, el cobre va abajo):
  KiCad dibuja B.Cu visto desde arriba. Al poner la hoja boca abajo sobre el cobre, la transferencia invierte la
  imagen y queda exactamente como el cobre visto desde abajo. Por eso el PDF de cobre se imprime SIN espejo.
"""
import csv
import sys
from collections import Counter
from pathlib import Path

import pcbnew

RAIZ = Path(__file__).resolve().parent.parent
BROCAS = [0.8, 1.0, 1.3, 3.2]          # brocas que tiene o necesita el equipo (E08); 3.2 = M3
mm = pcbnew.ToMM


def broca(d):
    """Broca más chica que no sea menor que el agujero de diseño (con 0.05 mm de tolerancia)."""
    for b in BROCAS:
        if b + 0.05 >= d:
            return b
    return round(d, 1)


def contorno(b):
    r = b.GetBoardEdgesBoundingBox()
    return mm(r.GetX()), mm(r.GetY()), mm(r.GetRight()), mm(r.GetBottom())


def agujeros(b, x0, y0):
    filas = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            d = mm(p.GetDrillSize().x)
            if d <= 0:
                continue
            pos = p.GetPosition()
            filas.append(dict(pieza=fp.GetReference(), pata=p.GetNumber() or "-", red=p.GetNetname() or "-",
                              x=round(mm(pos.x) - x0, 2), y=round(mm(pos.y) - y0, 2), d=round(d, 2),
                              broca=broca(d), cobre="no (NPTH)" if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH else "sí"))
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            pos = t.GetPosition()
            d = mm(t.GetDrillValue())
            filas.append(dict(pieza="VIA", pata="-", red=t.GetNetname(), x=round(mm(pos.x) - x0, 2),
                              y=round(mm(pos.y) - y0, 2), d=round(d, 2), broca=broca(d), cobre="sí (puente)"))
    filas.sort(key=lambda f: (f["y"], f["x"]))
    for i, f in enumerate(filas, 1):
        f["id"] = f"H{i:03d}"
    return filas


def regla(b, x0, y1, capa):
    """Regla de 50 mm bajo el contorno, en la capa indicada, para comprobar que la impresión salió 1:1."""
    objs = []
    y = y1 + 4
    for xa, ya, xb, yb in [(x0, y, x0 + 50, y), (x0, y - 1.5, x0, y + 1.5), (x0 + 50, y - 1.5, x0 + 50, y + 1.5)]:
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(xa), pcbnew.FromMM(ya)))
        s.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(xb), pcbnew.FromMM(yb)))
        s.SetLayer(capa)
        s.SetWidth(pcbnew.FromMM(0.3))
        b.Add(s)
        objs.append(s)
    t = pcbnew.PCB_TEXT(b)
    t.SetText("50 mm: medir con regla; si no mide 50 mm, la impresion NO esta a escala")
    t.SetLayer(capa)
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.5), pcbnew.FromMM(1.5)))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x0), pcbnew.FromMM(y + 3)))
    b.Add(t)
    objs.append(t)
    return objs


def agrupar_puentes(tramos):
    """Une los tramos F.Cu que se tocan: cada grupo es UN puente de alambre real."""
    par = {}

    def raiz(a):
        par.setdefault(a, a)
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for t in tramos:
        par[raiz((t.GetStart().x, t.GetStart().y))] = raiz((t.GetEnd().x, t.GetEnd().y))
    grupos = {}
    for t in tramos:
        grupos.setdefault(raiz((t.GetStart().x, t.GetStart().y)), []).append(t)
    return list(grupos.values())


def trazar(b, carpeta, nombre, capas, espejo=False, marcas=True):
    pc = pcbnew.PLOT_CONTROLLER(b)
    po = pc.GetPlotOptions()
    po.SetOutputDirectory(str(carpeta))
    po.SetPlotFrameRef(False)
    po.SetAutoScale(False)
    po.SetScale(1)
    po.SetMirror(espejo)
    po.SetUseAuxOrigin(False)
    po.SetBlackAndWhite(True)
    po.SetDrillMarksType(pcbnew.DRILL_MARKS_SMALL_DRILL_SHAPE if marcas else pcbnew.DRILL_MARKS_NO_DRILL_SHAPE)
    po.SetPlotValue(False)
    po.SetPlotReference(True)
    po.SetPlotInvisibleText(False)
    po.SetSketchPadsOnFabLayers(False)
    pc.OpenPlotfile(nombre, pcbnew.PLOT_FORMAT_PDF, nombre)
    for c in capas:
        pc.SetLayer(c)
        pc.PlotLayer()
    pc.ClosePlot()
    return Path(pc.GetPlotFileName())


def exportar(placa):
    ruta = RAIZ / placa / f"{placa}.kicad_pcb"
    b = pcbnew.LoadBoard(str(ruta))
    out = RAIZ / placa / "fabricacion"
    out.mkdir(exist_ok=True)
    x0, y0, x1, y1 = contorno(b)
    hs = agujeros(b, x0, y0)

    with open(out / f"{placa}_perforaciones.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["id", "pieza", "pata", "red", "x", "y", "d", "broca", "cobre"])
        w.writeheader()
        w.writerows(hs)
    puentes = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetLayer() == pcbnew.F_Cu]
    with open(out / f"{placa}_puentes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["puente", "red", "tramos", "largo_mm"])
        grupos = agrupar_puentes(puentes)
        for i, g in enumerate(grupos, 1):
            w.writerow([f"P{i:02d}", g[0].GetNetname(), len(g), round(sum(mm(t.GetLength()) for t in g), 1)])
    largo = sum(mm(t.GetLength()) for t in puentes)

    # PDFs 1:1 (se agregan regla y textos de ID en una copia en memoria; el .kicad_pcb no se guarda)
    regla(b, x0, y1, pcbnew.B_Cu)
    cobre = trazar(b, out, f"{placa}_cobre_1a1", [pcbnew.B_Cu, pcbnew.Edge_Cuts])
    for o in list(b.Drawings()):
        if isinstance(o, (pcbnew.PCB_SHAPE, pcbnew.PCB_TEXT)) and o.GetLayer() == pcbnew.B_Cu:
            b.Remove(o)
    regla(b, x0, y1, pcbnew.Cmts_User)
    for h in hs:
        c = pcbnew.PCB_SHAPE(b)
        c.SetShape(pcbnew.SHAPE_T_CIRCLE)
        c.SetCenter(pcbnew.VECTOR2I(pcbnew.FromMM(x0 + h["x"]), pcbnew.FromMM(y0 + h["y"])))
        c.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x0 + h["x"] + h["d"] / 2), pcbnew.FromMM(y0 + h["y"])))
        c.SetLayer(pcbnew.Cmts_User)
        c.SetWidth(pcbnew.FromMM(0.15))
        b.Add(c)
        t = pcbnew.PCB_TEXT(b)
        t.SetText(h["id"][1:])
        t.SetLayer(pcbnew.Cmts_User)
        t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.7), pcbnew.FromMM(0.7)))
        t.SetTextThickness(pcbnew.FromMM(0.1))
        t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x0 + h["x"] + 1.1), pcbnew.FromMM(y0 + h["y"] - 1.1)))
        b.Add(t)
    mapa = trazar(b, out, f"{placa}_perforaciones", [pcbnew.Edge_Cuts, pcbnew.F_Fab, pcbnew.Cmts_User], marcas=True)

    cuenta = Counter(h["broca"] for h in hs)
    sin_unir = b.GetConnectivity().GetUnconnectedCount(False)
    (out / "LEEME.md").write_text(f"""# Fabricación casera — placa `{placa}`

Generado por `herramientas/exportar_fabricacion.py` desde `{placa}.kicad_pcb`. **No editar a mano: regenerar.**

| Dato | Valor |
|---|---|
| Tamaño de la placa | {x1 - x0:.1f} × {y1 - y0:.1f} mm |
| Agujeros | {len(hs)} ({", ".join(f"{n} con broca {k} mm" for k, n in sorted(cuenta.items()))}) |
| Puentes de alambre (pistas F.Cu) | **{len(grupos)} puentes**, {largo:.0f} mm de alambre en total (`{placa}_puentes.csv`) |
| Conexiones sin rutear | **{sin_unir}** {"→ NO fabricar todavía" if sin_unir else "(ruteo completo)"} |

## Archivos
- `{cobre.name}`: patrón de cobre. Imprimir en **láser**, al **100 %** ("tamaño real", sin "ajustar a página"),
  **sin espejo**. Antes de planchar, medir la regla: debe dar 50 mm exactos.
- `{mapa.name}`: mapa de perforaciones visto desde los **componentes**, con el número de cada agujero (H###).
- `{placa}_perforaciones.csv`: coordenadas en mm desde la **esquina superior izquierda** de la placa vista desde
  los componentes (X a la derecha, Y hacia abajo), diámetro de diseño y broca sugerida.

## Orientación
El cobre va en la cara de abajo (B.Cu). La hoja se pone **boca abajo** sobre el cobre: la transferencia invierte
la imagen y queda como debe verse el cobre desde abajo. Por eso se imprime sin espejo. Las marcas pequeñas en el
centro de cada pad guían la broca (se taladra desde el cobre, después del ataque).
""", encoding="utf-8")
    print(f"{placa}: {len(hs)} agujeros, {len(grupos)} puentes ({largo:.0f} mm), {sin_unir} sin rutear -> {out}")


if __name__ == "__main__":
    for p in sys.argv[1:] or ["principal", "sensores"]:
        exportar(p)

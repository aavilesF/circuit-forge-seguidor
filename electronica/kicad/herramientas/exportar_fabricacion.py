#!/usr/bin/env python3.12
"""Archivos para fabricar en casa una PCB DE DOBLE CARA (planchado / transferencia de tóner + cloruro férrico).

Uso: python3.12 exportar_fabricacion.py principal|sensores

Genera en <placa>/fabricacion/:
  <placa>-<placa>_cara_abajo_1a1.pdf   Cobre de la cara de ABAJO (B.Cu) + contorno, SIN espejo, escala 1:1.
  <placa>-<placa>_cara_arriba_1a1.pdf  Cobre de la cara de ARRIBA (F.Cu) + contorno, EN ESPEJO, escala 1:1.
  <placa>-<placa>_perforaciones.pdf    Mapa de perforaciones 1:1 visto desde ARRIBA (componentes), con el número de
                                       cada agujero; las vías se marcan con "V".
  <placa>_perforaciones.csv            ID, pieza, pata, red, X, Y (mm desde la esquina superior izquierda vista desde
                                       arriba), diámetro, broca y tipo (pata / vía / montaje).
  <placa>_soldar_arriba.csv            Patas con pista en la cara de arriba: se sueldan por arriba (en piezas montadas
                                       arriba, ADEMÁS de por abajo; los TCRT5000 van montados abajo y se sueldan arriba).
  LEEME.md                             Resumen y procedimiento.

Sin metalizado:
  * Cada VÍA es un agujero de 0.8 mm con un alambre (pata cortada de resistencia) soldado en las dos caras.
  * Una pata con pista arriba se suelda también arriba; el enrutador solo hace eso en piezas que lo permiten
    (resistencias, diodos y transistores: ruteador.SOLDABLE_ARRIBA).

Orientación: KiCad dibuja las dos caras vistas desde arriba. La transferencia invierte la imagen:
  * cara de abajo: se imprime tal cual (sin espejo) y al planchar queda como se ve el cobre desde abajo;
  * cara de arriba: se imprime EN ESPEJO y al planchar queda derecha vista desde arriba.
Alineación: cada agujero M3 lleva una diana (círculo + cruz) en las dos caras; se taladran primero los M3 y cada hoja
se alinea centrando sus dianas en esos agujeros.
"""
import csv
import sys
from collections import Counter
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).parent))
from ruteador import capas_accesibles  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
BROCAS = [0.8, 1.0, 1.3, 3.2]          # brocas del equipo (E08); 3.2 = M3
mm = pcbnew.ToMM
MM = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))


def broca(d):
    for b in BROCAS:
        if b + 0.05 >= d:
            return b
    return round(d, 1)


def linea(b, capa, x1, y1, x2, y2, w=0.3):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(V(x1, y1)); s.SetEnd(V(x2, y2))
    s.SetLayer(capa); s.SetWidth(MM(w))
    b.Add(s)


def circulo(b, capa, x, y, r, w=0.3):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    s.SetCenter(V(x, y)); s.SetEnd(V(x + r, y))
    s.SetLayer(capa); s.SetWidth(MM(w))
    b.Add(s)


def texto(b, capa, txt, x, y, tam=1.5, espejo=False):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(txt); t.SetLayer(capa)
    t.SetTextSize(V(tam, tam)); t.SetTextThickness(MM(tam * 0.15))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    t.SetMirrored(espejo)
    t.SetPosition(V(x, y))
    b.Add(t)


def agujeros(b, x0, y0):
    filas = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            d = mm(p.GetDrillSize().x)
            if d <= 0:
                continue
            pos = p.GetPosition()
            npth = p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH
            filas.append(dict(pieza=fp.GetReference(), pata=p.GetNumber() or "-", red=p.GetNetname() or "-",
                              x=round(mm(pos.x) - x0, 2), y=round(mm(pos.y) - y0, 2), d=round(d, 2), broca=broca(d),
                              tipo=("montaje / alineación" if d < 5 else "hueco") if npth else "pata"))
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            pos = t.GetPosition()
            d = mm(t.GetDrillValue())
            filas.append(dict(pieza="VIA", pata="-", red=t.GetNetname(), x=round(mm(pos.x) - x0, 2),
                              y=round(mm(pos.y) - y0, 2), d=round(d, 2), broca=broca(d),
                              tipo="vía: alambre soldado en las dos caras"))
    filas.sort(key=lambda f: (f["y"], f["x"]))
    for i, f in enumerate(filas, 1):
        f["id"] = f"H{i:03d}"
    return filas


def patas_arriba(b):
    """Pastillas que tocan una pista F.Cu: hay que soldarlas también por arriba."""
    tramos = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetLayer() == pcbnew.F_Cu]
    salida = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH or not p.GetNetCode():
                continue
            pos = p.GetPosition()
            r = max(p.GetSize().x, p.GetSize().y) / 2
            for t in tramos:
                if t.GetNetCode() == p.GetNetCode() and (t.GetStart() - pos).EuclideanNorm() <= r or \
                        t.GetNetCode() == p.GetNetCode() and (t.GetEnd() - pos).EuclideanNorm() <= r:
                    salida.append((fp.GetReference(), p.GetNumber(), p.GetNetname(), 1 in capas_accesibles(fp),
                                   fp.GetLayer() == pcbnew.B_Cu))
                    break
    return salida


def dianas(b, capa, montajes, x0, y0):
    for h in montajes:
        x, y = x0 + h["x"], y0 + h["y"]
        circulo(b, capa, x, y, 2.6, 0.4)
        for dx, dy in ((1, 0), (0, 1)):
            linea(b, capa, x - 3.4 * dx, y - 3.4 * dy, x - 1.9 * dx, y - 1.9 * dy, 0.3)
            linea(b, capa, x + 1.9 * dx, y + 1.9 * dy, x + 3.4 * dx, y + 3.4 * dy, 0.3)


def regla(b, capa, x0, y1, leyenda, espejo=False):
    y = y1 + 4
    linea(b, capa, x0, y, x0 + 50, y)
    linea(b, capa, x0, y - 1.5, x0, y + 1.5)
    linea(b, capa, x0 + 50, y - 1.5, x0 + 50, y + 1.5)
    texto(b, capa, f"50 mm - {leyenda}", x0 + (50 if espejo else 0), y + 3, 1.4, espejo)


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
    pc.OpenPlotfile(nombre, pcbnew.PLOT_FORMAT_PDF, nombre)
    for c in capas:
        pc.SetLayer(c)
        pc.PlotLayer()
    pc.ClosePlot()
    return Path(pc.GetPlotFileName())


def quitar_dibujos(b, capas):
    for o in list(b.Drawings()):
        if o.GetLayer() in capas and isinstance(o, (pcbnew.PCB_SHAPE, pcbnew.PCB_TEXT)):
            b.Remove(o)


def exportar(placa):
    ruta = RAIZ / placa / f"{placa}.kicad_pcb"
    b = pcbnew.LoadBoard(str(ruta))
    out = RAIZ / placa / "fabricacion"
    out.mkdir(exist_ok=True)
    for viejo in out.glob("*"):
        viejo.unlink()
    e = b.GetBoardEdgesBoundingBox()
    x0, y0, x1, y1 = mm(e.GetX()), mm(e.GetY()), mm(e.GetRight()), mm(e.GetBottom())
    hs = agujeros(b, x0, y0)
    montajes = [h for h in hs if h["tipo"].startswith("montaje")]
    vias = [h for h in hs if h["pieza"] == "VIA"]
    arriba = patas_arriba(b)
    malas = [a for a in arriba if not a[3]]
    dos_caras = [a for a in arriba if not a[4]]

    with open(out / f"{placa}_perforaciones.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["id", "pieza", "pata", "red", "x", "y", "d", "broca", "tipo"])
        w.writeheader()
        w.writerows(hs)
    with open(out / f"{placa}_soldar_arriba.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pieza", "pata", "red", "se_puede_soldar_arriba", "como_se_suelda"])
        for a in sorted(arriba):
            w.writerow([a[0], a[1], a[2], "sí" if a[3] else "NO: revisar",
                        "solo arriba (pieza montada abajo)" if a[4] else "por las DOS caras"])

    # se aleja la placa 25 mm de la esquina de la hoja: las impresoras no imprimen los primeros milímetros
    dx, dy = 25 - x0, 25 - y0
    for it in list(b.GetFootprints()) + list(b.GetTracks()) + list(b.Drawings()):
        it.Move(V(dx, dy))
    x0, y0, x1, y1 = x0 + dx, y0 + dy, x1 + dx, y1 + dy
    # cara de abajo (sin espejo)
    dianas(b, pcbnew.B_Cu, montajes, x0, y0)
    regla(b, pcbnew.B_Cu, x0, y1, "CARA ABAJO, imprimir SIN espejo")
    abajo = trazar(b, out, f"{placa}_cara_abajo_1a1", [pcbnew.B_Cu, pcbnew.Edge_Cuts])
    quitar_dibujos(b, {pcbnew.B_Cu})
    # cara de arriba (en espejo); el texto se escribe ya invertido para que se lea al imprimir en espejo
    dianas(b, pcbnew.F_Cu, montajes, x0, y0)
    regla(b, pcbnew.F_Cu, x0, y1, "CARA ARRIBA, impresa EN ESPEJO", espejo=True)
    arr = trazar(b, out, f"{placa}_cara_arriba_1a1", [pcbnew.F_Cu, pcbnew.Edge_Cuts], espejo=True)
    quitar_dibujos(b, {pcbnew.F_Cu})
    # mapa de perforaciones (vista desde arriba)
    for h in hs:
        circulo(b, pcbnew.Cmts_User, x0 + h["x"], y0 + h["y"], h["d"] / 2, 0.15)
        etiqueta = "V" + h["id"][1:] if h["pieza"] == "VIA" else h["id"][1:]
        texto(b, pcbnew.Cmts_User, etiqueta, x0 + h["x"] + 1.0, y0 + h["y"] - 1.0, 0.7)
    regla(b, pcbnew.Cmts_User, x0, y1, "mapa de perforaciones visto desde ARRIBA")
    mapa = trazar(b, out, f"{placa}_perforaciones", [pcbnew.Edge_Cuts, pcbnew.F_Fab, pcbnew.Cmts_User])

    cuenta = Counter(h["broca"] for h in hs)
    sin_unir = b.GetConnectivity().GetUnconnectedCount(False)
    largo_arriba = sum(mm(t.GetLength()) for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetLayer() == pcbnew.F_Cu)
    estado = "**NO fabricar todavía**: faltan conexiones" if sin_unir else "ruteo completo"
    (out / "LEEME.md").write_text(f"""# Fabricación casera de doble cara — placa `{placa}`

Generado por `herramientas/exportar_fabricacion.py` desde `{placa}.kicad_pcb`. **No editar a mano: regenerar.**

| Dato | Valor |
|---|---|
| Tamaño | {x1 - x0:.1f} × {y1 - y0:.1f} mm |
| Agujeros | {len(hs)} ({", ".join(f"{n} con broca {k} mm" for k, n in sorted(cuenta.items()))}) |
| Vías (alambre soldado por las dos caras) | **{len(vias)}** |
| Pistas en la cara de arriba | {largo_arriba:.0f} mm |
| Patas que se sueldan por las **dos** caras | {len(dos_caras)} (`{placa}_soldar_arriba.csv`){f"; **{len(malas)} en piezas difíciles de soldar arriba: revisar**" if malas else ""} |
| Patas de piezas montadas abajo (se sueldan solo por arriba) | {len(arriba) - len(dos_caras)} |
| Conexiones sin rutear | **{sin_unir}** → {estado} |

## Archivos
- `{abajo.name}`: cara de **abajo**. Imprimir en láser al **100 %**, **sin espejo**.
- `{arr.name}`: cara de **arriba**. Ya viene **en espejo**: imprimir al 100 % tal cual (no volver a invertir).
- `{mapa.name}`: perforaciones vistas desde arriba; "V###" = vía.
- `{placa}_perforaciones.csv`: X, Y en mm desde la esquina superior izquierda vista desde arriba.

## Procedimiento
1. Cortar la placa con 5 mm de sobra. Medir la regla de 50 mm de cada hoja: si no mide 50 mm, no sirve.
2. Taladrar **solo los agujeros M3** (broca 3.2) usando el mapa.
3. Planchar la cara de abajo centrando sus dianas en los agujeros M3. Luego la de arriba, igual.
4. Atacar con cloruro férrico las dos caras (proteger la que no se ataca si se hace por turnos). Limpiar el tóner.
5. Taladrar el resto desde cualquier cara usando las marcas del centro de cada pad.
6. Vías: meter un alambre en cada una y soldarlo por las dos caras; cortar el sobrante.
7. Soldar los componentes. En `{placa}_soldar_arriba.csv`, las patas marcadas "por las DOS caras" se sueldan arriba
   y abajo; las de piezas montadas abajo (sensores), solo arriba.
8. Antes de conectar nada: continuidad de cada vía con el multímetro.
""", encoding="utf-8")
    print(f"{placa}: {len(hs)} agujeros, {len(vias)} vías, {len(dos_caras)} patas por las dos caras "
          f"({len(malas)} difíciles), {largo_arriba:.0f} mm arriba, {sin_unir} sin rutear -> {out}")


if __name__ == "__main__":
    for p in sys.argv[1:] or ["principal", "sensores"]:
        exportar(p)

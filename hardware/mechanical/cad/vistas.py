"""Vistas del CAD: renders del robot completo (VTK fuera de pantalla) y planos acotados de las piezas fabricadas
(proyección de aristas con matplotlib). Lo usa generar_cad.py."""
from __future__ import annotations

import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


# ------------------------------------------------------------------ renders
def _polydata(forma, tol=0.05):
    import vtk
    v, t = forma.tessellate(tol, 0.35)
    pts = vtk.vtkPoints()
    for p in v:
        pts.InsertNextPoint(p.x, p.y, p.z)
    tri = vtk.vtkCellArray()
    for a, b, c in t:
        tri.InsertNextCell(3)
        tri.InsertCellPoint(a); tri.InsertCellPoint(b); tri.InsertCellPoint(c)
    pd = vtk.vtkPolyData()
    pd.SetPoints(pts); pd.SetPolys(tri)
    n = vtk.vtkPolyDataNormals()
    n.SetInputData(pd); n.SetFeatureAngle(35); n.SplittingOn(); n.Update()
    return n.GetOutput()


def renders(piezas, carpeta, ancho=2400, alto=1800, prefijo="robot"):
    """piezas: lista de (nombre, forma OCC (cq.Shape), (r, g, b)). Escribe <prefijo>_<vista>.png."""
    import vtk
    os.makedirs(carpeta, exist_ok=True)
    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)
    ren.SetBackground2(0.86, 0.89, 0.93)
    ren.GradientBackgroundOn()
    for _, forma, col in piezas:
        pd = _polydata(forma)
        m = vtk.vtkPolyDataMapper(); m.SetInputData(pd)
        a = vtk.vtkActor(); a.SetMapper(m)
        pr = a.GetProperty()
        pr.SetColor(*col); pr.SetSpecular(0.25); pr.SetSpecularPower(25); pr.SetAmbient(0.15); pr.SetDiffuse(0.85)
        ren.AddActor(a)
    # piso
    piso = vtk.vtkPlaneSource()
    piso.SetOrigin(-40, -70, 0); piso.SetPoint1(150, -70, 0); piso.SetPoint2(-40, 70, 0)
    mp = vtk.vtkPolyDataMapper(); mp.SetInputConnection(piso.GetOutputPort())
    ap = vtk.vtkActor(); ap.SetMapper(mp); ap.GetProperty().SetColor(0.93, 0.93, 0.90); ap.GetProperty().SetOpacity(0.55)
    ren.AddActor(ap)
    rw = vtk.vtkRenderWindow()
    rw.SetOffScreenRendering(1)
    rw.AddRenderer(ren)
    rw.SetSize(ancho, alto)
    rw.SetMultiSamples(8)
    centro = (50.0, 0.0, 10.0)
    vistas = {
        "isometrica": ((-110, 150, 140), (0, 0, 1), False),
        "isometrica_trasera": ((230, -150, 120), (0, 0, 1), False),
        "superior": ((50, 0, 400), (1, 0, 0), True),
        "inferior": ((50, 0, -400), (1, 0, 0), True),
        "lateral_izquierda": ((50, 400, 10), (0, 0, 1), True),
        "frontal": ((450, 0, 10), (0, 0, 1), True),
    }
    escritos = []
    for nombre, (pos, arriba, orto) in vistas.items():
        ap.SetVisibility(nombre not in ("inferior",))
        cam = ren.GetActiveCamera()
        cam.SetFocalPoint(*centro)
        cam.SetPosition(pos[0], pos[1], pos[2])
        cam.SetViewUp(*arriba)
        cam.SetParallelProjection(orto)
        ren.ResetCamera()
        cam.SetFocalPoint(*centro)
        if orto:
            cam.SetParallelScale({"superior": 78, "inferior": 78, "lateral_izquierda": 52}.get(nombre, 40))
        else:
            cam.Zoom(1.35)
        ren.ResetCameraClippingRange()
        rw.Render()
        w = vtk.vtkWindowToImageFilter(); w.SetInput(rw); w.Update()
        p = vtk.vtkPNGWriter()
        ruta = os.path.join(carpeta, f"{prefijo}_{nombre}.png")
        p.SetFileName(ruta); p.SetInputConnection(w.GetOutputPort()); p.Write()
        escritos.append(ruta)
    return escritos


# ------------------------------------------------------------------ planos
VISTAS_PLANO = {"superior (XY)": (0, 1), "frontal (XZ)": (0, 2), "lateral (YZ)": (1, 2)}


def _aristas(forma, eje_a, eje_b):
    lineas = []
    for e in forma.Edges():
        try:
            n = 24 if e.geomType() in ("CIRCLE", "BSPLINE", "ELLIPSE") else 2
            ps = [e.positionAt(i / (n - 1)) for i in range(n)]
        except Exception:
            continue
        lineas.append(([p.toTuple()[eje_a] for p in ps], [p.toTuple()[eje_b] for p in ps]))
    return lineas


def _cota(ax, p0, p1, desplaz, texto, vertical=False):
    """Cota con flechas entre p0 y p1 (coordenadas del dibujo), desplazada perpendicularmente."""
    if vertical:
        x = p0[0] + desplaz
        ax.annotate("", xy=(x, p0[1]), xytext=(x, p1[1]), arrowprops=dict(arrowstyle="<->", lw=0.7))
        ax.plot([p0[0], x], [p0[1], p0[1]], lw=0.4, color="0.4"); ax.plot([p1[0], x], [p1[1], p1[1]], lw=0.4, color="0.4")
        ax.text(x + 0.4 * math.copysign(1, desplaz), (p0[1] + p1[1]) / 2, texto, rotation=90, va="center",
                ha="left" if desplaz > 0 else "right", fontsize=7)
    else:
        y = p0[1] + desplaz
        ax.annotate("", xy=(p0[0], y), xytext=(p1[0], y), arrowprops=dict(arrowstyle="<->", lw=0.7))
        ax.plot([p0[0], p0[0]], [p0[1], y], lw=0.4, color="0.4"); ax.plot([p1[0], p1[0]], [p1[1], y], lw=0.4, color="0.4")
        ax.text((p0[0] + p1[0]) / 2, y + 0.3 * math.copysign(1, desplaz), texto, ha="center",
                va="bottom" if desplaz > 0 else "top", fontsize=7)


def plano_pieza(nombre, forma, carpeta, material, notas=()):
    """Hoja con 3 vistas en alambre, cotas generales y tabla de agujeros (círculos de la vista superior)."""
    os.makedirs(carpeta, exist_ok=True)
    bb = forma.BoundingBox()
    fig, axs = plt.subplots(1, 3, figsize=(16.5, 7.4))
    for ax, (titulo, (a, b)) in zip(axs, VISTAS_PLANO.items()):
        for xs, ys in _aristas(forma, a, b):
            ax.plot(xs, ys, color="k", lw=0.6)
        lo = (bb.xmin, bb.ymin, bb.zmin); hi = (bb.xmax, bb.ymax, bb.zmax)
        _cota(ax, (lo[a], lo[b]), (hi[a], lo[b]), -2.5, f"{hi[a] - lo[a]:.2f}")
        _cota(ax, (hi[a], lo[b]), (hi[a], hi[b]), 2.5, f"{hi[b] - lo[b]:.2f}", vertical=True)
        ax.set_title(f"Vista {titulo}", fontsize=9)
        ax.set_aspect("equal"); ax.margins(0.18)
        ax.tick_params(labelsize=6); ax.grid(alpha=0.15)
        ax.set_xlabel("xyz"[a] + " [mm, marco del robot]", fontsize=7); ax.set_ylabel("xyz"[b] + " [mm]", fontsize=7)
    agujeros = []
    for e in forma.Edges():
        if e.geomType() == "CIRCLE":
            c = e.Center(); r = e.radius()
            clave = (round(c.x, 2), round(c.y, 2), round(2 * r, 2))
            if 1.0 < 2 * r < 8.0 and clave not in [(h[0], h[1], h[2]) for h in agujeros]:
                agujeros.append(clave)
    agujeros = sorted(set(agujeros))
    filas = [f"Ø{d:.2f} en x={x:.2f}, y={y:.2f}" for x, y, d in agujeros][:12]
    texto = (f"{nombre}\nMaterial: {material}\nVolumen: {forma.Volume():.0f} mm³   Envolvente: "
             f"{bb.xlen:.2f} × {bb.ylen:.2f} × {bb.zlen:.2f} mm\nCotas en mm. Coordenadas en el marco del robot "
             f"(x adelante desde el eje de ruedas, y izquierda, z desde el piso).\n"
             + ("Círculos (agujeros y alojamientos):\n  " + "\n  ".join(filas) if filas else "")
             + ("\n" + "\n".join(notas) if notas else ""))
    fig.text(0.01, 0.01, texto, fontsize=7, va="bottom", family="monospace")
    fig.suptitle(f"Plano de fabricación — {nombre}", fontsize=11)
    fig.tight_layout(rect=(0, 0.27, 1, 0.95))
    rutas = []
    for ext in ("png", "svg"):
        r = os.path.join(carpeta, f"{nombre}.{ext}")
        fig.savefig(r, dpi=200 if ext == "png" else None)
        rutas.append(r)
    plt.close(fig)
    return rutas


def plano_conjunto(contornos, cotas, carpeta, nombre="robot_conjunto", titulo="Robot completo"):
    """contornos: {vista: [(xs, ys, color)]}; cotas: {vista: [(p0, p1, desplaz, texto, vertical)]}."""
    os.makedirs(carpeta, exist_ok=True)
    fig, axs = plt.subplots(1, len(contornos), figsize=(18, 6.5), gridspec_kw=dict(width_ratios=[1.6, 1.0, 1.0][:len(contornos)]))
    for ax, (vista, lineas) in zip(axs, contornos.items()):
        for xs, ys, col in lineas:
            ax.plot(xs, ys, color=col, lw=0.5)
        for p0, p1, d, t, vert in cotas.get(vista, []):
            _cota(ax, p0, p1, d, t, vertical=vert)
        ax.set_title(vista, fontsize=9); ax.set_aspect("equal"); ax.margins(0.12)
        ax.tick_params(labelsize=6); ax.grid(alpha=0.15)
    fig.suptitle(titulo, fontsize=11)
    fig.tight_layout()
    rutas = []
    for ext in ("png", "svg"):
        r = os.path.join(carpeta, f"{nombre}.{ext}")
        fig.savefig(r, dpi=200 if ext == "png" else None)
        rutas.append(r)
    plt.close(fig)
    return rutas

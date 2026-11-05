"""V2 · Vistas del CAD (VTK fuera de pantalla) con sólidos de CadQuery y mallas (los OBJ del usuario).
Los planos de pieza reutilizan hardware/mechanical/cad/vistas.py de V1 (sin cambios)."""
from __future__ import annotations

import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "hardware", "mechanical", "cad"))
import vistas as V1  # noqa: E402

plano_pieza = V1.plano_pieza


def _poly_malla(m):
    import vtk
    pts = vtk.vtkPoints()
    for p in m.vertices:
        pts.InsertNextPoint(*p)
    tri = vtk.vtkCellArray()
    for a, b, c in m.faces:
        tri.InsertNextCell(3); tri.InsertCellPoint(int(a)); tri.InsertCellPoint(int(b)); tri.InsertCellPoint(int(c))
    pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(tri)
    n = vtk.vtkPolyDataNormals(); n.SetInputData(pd); n.SetFeatureAngle(35); n.SplittingOn(); n.Update()
    return n.GetOutput()


VISTAS = {
    "isometrica": ((-120, 170, 150), (0, 0, 1), False, None),
    "isometrica_trasera": ((240, -170, 130), (0, 0, 1), False, None),
    "superior": ((45, 0, 400), (1, 0, 0), True, 92),
    "inferior": ((45, 0, -400), (1, 0, 0), True, 92),
    "lateral_izquierda": ((45, 400, 15), (0, 0, 1), True, 50),
    "frontal": ((450, 0, 15), (0, 0, 1), True, 40),
    "trasera": ((-400, 0, 15), (0, 0, 1), True, 40),
}


def renders(piezas, mallas, carpeta, ancho=1800, alto=1350, prefijo="robot", vistas=None):
    import vtk
    os.makedirs(carpeta, exist_ok=True)
    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1); ren.SetBackground2(0.86, 0.89, 0.93); ren.GradientBackgroundOn()
    datos = [(V1._polydata(f.val() if len(f.vals()) == 1 else __import__("cadquery").Compound.makeCompound(f.vals())), c)
             for _, f, c in piezas]
    datos += [(_poly_malla(m), c) for m, c in mallas]
    for pd, col in datos:
        m = vtk.vtkPolyDataMapper(); m.SetInputData(pd)
        a = vtk.vtkActor(); a.SetMapper(m)
        pr = a.GetProperty(); pr.SetColor(*col); pr.SetSpecular(0.25); pr.SetSpecularPower(25); pr.SetAmbient(0.15); pr.SetDiffuse(0.85)
        ren.AddActor(a)
    piso = vtk.vtkPlaneSource()
    piso.SetOrigin(-60, -75, 0); piso.SetPoint1(150, -75, 0); piso.SetPoint2(-60, 75, 0)
    mp = vtk.vtkPolyDataMapper(); mp.SetInputConnection(piso.GetOutputPort())
    ap = vtk.vtkActor(); ap.SetMapper(mp); ap.GetProperty().SetColor(0.93, 0.93, 0.90); ap.GetProperty().SetOpacity(0.5)
    ren.AddActor(ap)
    rw = vtk.vtkRenderWindow(); rw.SetOffScreenRendering(1); rw.AddRenderer(ren); rw.SetSize(ancho, alto); rw.SetMultiSamples(8)
    centro = (45.0, 0.0, 12.0)
    out = []
    for nombre, (pos, arriba, orto, escala) in VISTAS.items():
        if vistas and nombre not in vistas:
            continue
        ap.SetVisibility(nombre != "inferior")
        cam = ren.GetActiveCamera()
        cam.SetFocalPoint(*centro); cam.SetPosition(*pos); cam.SetViewUp(*arriba); cam.SetParallelProjection(orto)
        ren.ResetCamera(); cam.SetFocalPoint(*centro)
        if orto:
            cam.SetParallelScale(escala)
        else:
            cam.Zoom(1.3)
        ren.ResetCameraClippingRange(); rw.Render()
        w = vtk.vtkWindowToImageFilter(); w.SetInput(rw); w.Update()
        p = vtk.vtkPNGWriter(); ruta = os.path.join(carpeta, f"{prefijo}_{nombre}.png")
        p.SetFileName(ruta); p.SetInputConnection(w.GetOutputPort()); p.Write()
        out.append(ruta)
    return out

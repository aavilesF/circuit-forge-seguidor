#!/usr/bin/env python3
"""Modelos 3D propios (STEP) para las dos partes sin modelo en la biblioteca oficial de KiCad 9.0.7:
  AMASS_XT30UPB-M.step : APROXIMADO. Contorno 10.2 × 5.2 mm de la capa F.Fab de la huella oficial KiCad
                         (con el chaflán del lado −), altura 8.0 mm [E], dos pines Ø1.5 mm (pads de la huella).
  Fuse_1812L.step      : APROXIMADO. 1812 (4.5 × 3.2 mm), espesor 1.0 mm [E] (Littelfuse 1812L, rango de la serie).
El origen coincide con el de la huella (pad 1)."""
import os
import cadquery as cq

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kicad", "3d")

xt = (cq.Workplane("XY").polyline([(-2.6, -1.3), (-0.9, -2.6), (7.6, -2.6), (7.6, 2.6), (-0.9, 2.6), (-2.6, 1.3)]).close()
      .extrude(8.0))
xt = xt.cut(cq.Workplane("XY").circle(1.0).extrude(9).translate((0, 0, 1.5))).cut(
    cq.Workplane("XY").circle(1.0).extrude(9).translate((5.0, 0, 1.5)))
pines = cq.Workplane("XY").circle(0.75).extrude(11.0).translate((0, 0, -3.0)).union(
    cq.Workplane("XY").circle(0.75).extrude(11.0).translate((5.0, 0, -3.0)))
cq.exporters.export(xt.union(pines), os.path.join(D, "AMASS_XT30UPB-M.step"))

f = cq.Workplane("XY").box(4.5, 3.2, 1.0, centered=(True, True, False))
cq.exporters.export(f, os.path.join(D, "Fuse_1812L.step"))
print("modelos propios escritos en", os.path.normpath(D))

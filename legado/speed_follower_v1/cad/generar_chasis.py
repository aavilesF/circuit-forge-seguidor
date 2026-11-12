"""Chasis paramétrico del Plan B (módulos sobre chasis impreso). Uso: python3 generar_chasis.py

Ejes: x hacia adelante, y a la izquierda, z hacia arriba; origen en el piso bajo el centro del eje de ruedas.
Todo lo marcado MEDIR es nominal: confirmar con la pieza real ANTES de imprimir.
Uso: python3 generar_chasis.py [llanta34|llanta43]  (sin argumento genera ambos)
Salidas por variante: chasis_planB_<variante>.stl / .png / .txt
"""
from dataclasses import dataclass, asdict
import math, sys
import numpy as np
import manifold3d as m3
import trimesh

@dataclass
class P:
    nombre: str = "llanta34"
    # Ruedas y motores
    diam_rueda: float = 34.0        # llanta N20 34 x 7 de UNIT (agotada al 31 oct) - MEDIR la comprada
    ancho_rueda: float = 7.0
    via: float = 85.0               # centro a centro de llantas (simulación: W = 85 mm)
    motor_ancho: float = 12.0       # micro metal gearmotor / N20: 12 x 10 mm (MEDIR)
    motor_alto: float = 10.0
    motor_largo: float = 24.0       # reductora + motor, sin eje trasero (MEDIR; con encoder es mayor)
    hueco_rueda: float = 2.0        # de la cara de la reductora a la cara interior de la llanta
    # Placa
    espesor: float = 3.0
    ancho_placa: float = 70.0       # se angosta junto a las llantas si hace falta
    x_trasero: float = -30.0
    ancho_cuello: float = 30.0
    # Sensores (barra 65.7 x 16 del clon UNIT de QTR-8A: MEDIR, incluidos agujeros)
    L: float = 130.0                # eje de ruedas a la línea de sensores (SF-4)
    sensor_ancho: float = 65.7
    sensor_fondo: float = 16.0
    sensor_altura_piso: float = 8.0  # MEDIR: el vendedor indica 8-12 mm; Pololu original 3 mm
    sensor_grosor: float = 4.0       # PCB + componentes del lado superior (MEDIR)
    # Apoyo delantero: "Mini rueda universal 3Pi N20" de UNIT, 22 x 16 x 15 mm (MEDIR agujeros y altura)
    x_caster: float = 109.0
    caster_sep: float = 15.0
    caster_agujero: float = 2.2
    caster_altura: float = 15.0      # del piso a la cara de montaje
    # Módulos
    bat: tuple = (55.0, 30.0, 14.0)  # LiPo 2S (MEDIR)
    mux: tuple = (18.0, 41.0)        # módulo 74HC4067 de 16 canales, montado de través (MEDIR)
    esp: tuple = (55.0, 28.0)        # ESP32 DevKit 38 pines (UNIT: 55 x 28 mm)
    esp_altura_rieles: float = 10.0  # libra los pines por debajo
    pared: float = 1.6
    densidad_pla: float = 1.24       # g/cm³

PRESETS = {
    "llanta34": P(),
    # Llanta 43 x 19 (la que sí hay en UNIT): con vía de 85 el robot mediría 104 mm de ancho (> 100).
    "llanta43": P(nombre="llanta43", diam_rueda=43.0, ancho_rueda=19.0, via=77.0),
}

def caja(x0, x1, y0, y1, z0, z1):
    return m3.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])

def cilindro_z(x, y, z0, z1, d, n=32):
    return m3.Manifold.cylinder(z1 - z0, d / 2, d / 2, n).translate([x, y, z0])

def construir(p: P):
    r = p.diam_rueda / 2
    z_top = r - p.motor_alto / 2                    # el motor (eje = eje de rueda) se apoya sobre la placa
    z_bot = z_top - p.espesor
    avisos = []
    if z_bot < 4:
        avisos.append(f"placa a {z_bot:.1f} mm del piso: muy baja")
    y_cara_interior = p.via / 2 - p.ancho_rueda / 2
    y_reductora = y_cara_interior - p.hueco_rueda
    y_motor_int = y_reductora - p.motor_largo
    if y_motor_int < 1:
        avisos.append("los motores chocan en el centro")
    # Placa: angosta junto a las llantas si la ancha no cabe
    semi_libre = y_cara_interior - 1.5
    semi_ancha = p.ancho_placa / 2
    if semi_ancha <= semi_libre:
        semi_rueda, x_ancha = semi_ancha, p.x_trasero
    else:
        semi_rueda, x_ancha = semi_libre, r + 3.0
    bx, by, bz = p.bat
    ex, ey = p.esp
    if 2 * semi_rueda < 2 * (p.motor_ancho / 2 + 6):
        avisos.append("placa demasiado angosta junto a las llantas")
    bx0 = max(8.0, x_ancha + p.pared)
    x_fin_ancho = bx0 + bx + p.pared + 2
    by0 = -semi_ancha + 2
    ey0 = by0 + by + p.pared + 1.5
    if ey0 + ey + 1.2 > semi_ancha:
        avisos.append("batería + ESP32 no caben a lo ancho")

    # Nivel del frente: lo fija el más alto de (placa, cara del caster, techo de la barra de sensores)
    z_sensor_techo = p.sensor_altura_piso + p.sensor_grosor
    z_f = max(z_bot, p.caster_altura, z_sensor_techo)
    separador = z_f - z_sensor_techo              # separadores entre barra y almohadilla
    x_pad0, x_pad1 = p.L - p.sensor_fondo / 2 - 2, p.L + p.sensor_fondo / 2 + 2
    mx, my = p.mux
    x_rampa = x_fin_ancho + min(18.0, max(4.0, p.x_caster - 12 - mx - 1 - x_fin_ancho))
    x_mux = x_rampa + 1
    if x_mux + mx > p.x_caster - 11 + 0.01:      # el caster mide 22 mm: su cuerpo empieza 11 mm antes del centro
        avisos.append("el multiplexor no cabe entre la rampa y el caster")
    if p.x_caster + 11 > p.L - p.sensor_fondo / 2:
        avisos.append("el caster invade la barra de sensores")

    piezas = []
    piezas.append(caja(p.x_trasero, x_fin_ancho, -semi_rueda, semi_rueda, z_bot, z_top))
    if x_ancha > p.x_trasero:
        piezas.append(caja(x_ancha, x_fin_ancho, -semi_ancha, semi_ancha, z_bot, z_top))
    else:
        piezas.append(caja(p.x_trasero, x_fin_ancho, -semi_ancha, semi_ancha, z_bot, z_top))
    a = caja(x_fin_ancho - 1, x_fin_ancho, -p.ancho_cuello / 2, p.ancho_cuello / 2, z_bot, z_top)
    b = caja(x_rampa, x_rampa + 0.1, -p.ancho_cuello / 2, p.ancho_cuello / 2, z_f, z_f + p.espesor)
    piezas.append(m3.Manifold.batch_hull([a, b]))
    piezas.append(caja(x_rampa, x_pad0 + 1, -p.ancho_cuello / 2, p.ancho_cuello / 2, z_f, z_f + p.espesor))
    piezas.append(caja(x_mux - 1, x_mux + mx + 1, -my / 2 - 1, my / 2 + 1, z_f, z_f + p.espesor))   # ensanche para el mux
    piezas.append(caja(x_pad0, x_pad1, -p.sensor_ancho / 2 - 2, p.sensor_ancho / 2 + 2, z_f, z_f + p.espesor))
    if p.caster_altura < z_f - 0.5:
        piezas.append(caja(p.x_caster - 6, p.x_caster + 6, -p.caster_sep / 2 - 4, p.caster_sep / 2 + 4, p.caster_altura, z_f + 0.01))

    # Cunas de motor: paredes delante y detrás del motor + tope interior
    for s in (1, -1):
        y_a, y_b = sorted([s * y_motor_int, s * (y_reductora - 1)])
        for xs in (1, -1):
            x_in = xs * (p.motor_ancho / 2 + 0.2)
            x0, x1 = sorted([x_in, x_in + xs * 2.0])
            piezas.append(caja(x0, x1, y_a, y_b, z_top, z_top + p.motor_alto * 0.8))
        if y_motor_int > 3:
            y_t0, y_t1 = sorted([s * (y_motor_int - 0.3), s * (y_motor_int - 2.3)])
            piezas.append(caja(-p.motor_ancho / 2, p.motor_ancho / 2, y_t0, y_t1, z_top, z_top + p.motor_alto * 0.6))

    # Bandeja de batería (paredes bajas) y rieles del ESP32
    hb = 5.0
    for (x0, x1, y0, y1) in [(bx0 - p.pared, bx0, by0, by0 + by), (bx0 + bx, bx0 + bx + p.pared, by0, by0 + by),
                             (bx0 - p.pared, bx0 + bx + p.pared, by0 + by, by0 + by + p.pared)]:
        piezas.append(caja(x0, x1, y0, y1, z_top, z_top + hb))
    for y_r in (ey0, ey0 + ey - 3):
        piezas.append(caja(bx0, bx0 + ex, y_r, y_r + 3, z_top, z_top + p.esp_altura_rieles))
    piezas.append(caja(bx0, bx0 + ex, ey0 - 1.2, ey0, z_top, z_top + p.esp_altura_rieles + 2))            # labios
    piezas.append(caja(bx0, bx0 + ex, ey0 + ey, ey0 + ey + 1.2, z_top, z_top + p.esp_altura_rieles + 2))

    cuerpo = m3.Manifold.batch_boolean(piezas, m3.OpType.Add)

    # Reglamento: caber en 200 x 100 mm (largo x ancho), contando llantas y barra de sensores
    largo = x_pad1 - min(p.x_trasero, -r)
    ancho = max(p.via + p.ancho_rueda, p.sensor_ancho + 4, p.ancho_placa)
    if largo > 195: avisos.append(f"largo {largo:.1f} mm: menos de 5 mm de margen sobre 200")
    if ancho > 97: avisos.append(f"ancho {ancho:.1f} mm: menos de 3 mm de margen sobre 100")

    restas = []
    for s in (1, -1):                      # agujeros del caster
        restas.append(cilindro_z(p.x_caster, s * p.caster_sep / 2, -1, 60, p.caster_agujero))
    for s in (1, -1):                      # cinchos de motor (2 por motor)
        for yy in (y_motor_int + 5, y_reductora - 6):
            for xs in (1, -1):
                xc = xs * (p.motor_ancho / 2 + 3.6)
                restas.append(caja(xc - 1.0, xc + 1.0, s * yy - 2.2, s * yy + 2.2, -1, 60))
    for xx in (bx0 + 12, bx0 + bx - 12):   # velcro de batería
        restas.append(caja(xx - 1.2, xx + 1.2, by0 + 2, by0 + by - 2, -1, z_top + 0.01))
    for xx in (bx0 + 8, bx0 + ex - 8):     # cinchos del ESP32
        restas.append(caja(xx - 2.2, xx + 2.2, ey0 + 3.5, ey0 + 5.5, -1, z_top + 0.01))
        restas.append(caja(xx - 2.2, xx + 2.2, ey0 + ey - 5.5, ey0 + ey - 3.5, -1, z_top + 0.01))
    for xx in (p.L - 4.5, p.L + 4.5):      # ranuras de la barra (posición real de agujeros: MEDIR)
        restas.append(caja(xx - 1.3, xx + 1.3, -p.sensor_ancho / 2 + 2, -p.sensor_ancho / 2 + 14, -1, 60))
        restas.append(caja(xx - 1.3, xx + 1.3, p.sensor_ancho / 2 - 14, p.sensor_ancho / 2 - 2, -1, 60))
    restas.append(caja(p.L - 1.5, p.L + 1.5, -18, 18, -1, 60))   # paso de cables
    for xx in (p.x_trasero + 5, p.x_trasero + 18):                # zona trasera: driver y regulador
        for yy in (-0.8 * semi_rueda, -0.3 * semi_rueda, 0.3 * semi_rueda, 0.8 * semi_rueda):
            restas.append(caja(xx - 1.0, xx + 1.0, yy - 2.2, yy + 2.2, -1, z_top + 0.01))
    for yy in (-my / 2 + 4, my / 2 - 4):  # cinchos del multiplexor
        restas.append(caja(x_mux + 3, x_mux + mx - 3, yy - 1.0, yy + 1.0, -1, 60))
    corte = m3.Manifold.batch_boolean(restas, m3.OpType.Add)
    cuerpo = cuerpo - corte
    info = dict(largo=largo, ancho=ancho, z_placa=(z_bot, z_top), z_f=z_f, separador=separador,
                y_motor=(y_motor_int, y_reductora), bat=(bx0, by0), esp=(bx0, ey0), x_mux=x_mux,
                semi_rueda=semi_rueda)
    return cuerpo, avisos, info

def a_trimesh(man):
    mesh = man.to_mesh()
    tm = trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts), process=False)
    return tm   # sin "process": manifold ya entrega una malla cerrada e indexada

def masa_estimada(vol_mm3, dens):
    # Pieza de paredes delgadas (3 mm): casi todo es perímetro y tapas. Se dan tres escenarios de relleno efectivo.
    return {f: vol_mm3 / 1000 * dens * f for f in (0.6, 0.8, 1.0)}

def vista(tm, p, info, ruta):
    """Vista superior y lateral con los componentes nominales dibujados encima (contorno punteado)."""
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Rectangle, Circle
    tri = tm.vertices[tm.faces]
    n = tm.face_normals
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 8.5), gridspec_kw={"height_ratios": [2.3, 1]})
    sup = n[:, 2] > 0.5
    zc = tri[sup][:, :, 2].mean(axis=1)
    orden = np.argsort(zc)
    pc = PolyCollection(tri[sup][orden][:, :, :2], array=zc[orden], cmap="Blues", edgecolors="none")
    pc.set_clim(5, 25)
    a1.add_collection(pc)
    r = p.diam_rueda / 2
    yi, yr = info["y_motor"]
    def caja2(ax, x, y, w, h, c, t):
        ax.add_patch(Rectangle((x, y), w, h, fill=False, ls="--", lw=1.2, ec=c))
        if t: ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=8, color=c)
    for s in (1, -1):
        caja2(a1, -r, s * p.via / 2 - p.ancho_rueda / 2, 2 * r, p.ancho_rueda, "#444", "rueda")
        y0 = min(s * yi, s * yr)
        caja2(a1, -p.motor_ancho / 2, y0, p.motor_ancho, p.motor_largo, "#a33", "motor")
    bx, by, bz = p.bat
    caja2(a1, *info["bat"], bx, by, "#a60", "batería 2S")
    caja2(a1, *info["esp"], p.esp[0], p.esp[1], "#063", "ESP32")
    caja2(a1, p.L - p.sensor_fondo / 2, -p.sensor_ancho / 2, p.sensor_fondo, p.sensor_ancho, "#606", "sensores")
    caja2(a1, info["x_mux"], -p.mux[1] / 2, p.mux[0], p.mux[1], "#555", "mux")
    sr = info["semi_rueda"]
    caja2(a1, p.x_trasero + 1, -sr + 2, 21, sr - 3, "#555", "driver")
    caja2(a1, p.x_trasero + 1, 1, 21, sr - 3, "#555", "regulador")
    a1.add_patch(Rectangle((p.x_caster - 11, -8), 22, 16, fill=False, ls=":", ec="#000"))
    a1.text(p.x_caster, -11, "caster (abajo)", ha="center", va="top", fontsize=8)
    a1.axvline(0, color="#999", lw=0.6); a1.axvline(p.L, color="#999", lw=0.6)
    a1.annotate("", xy=(p.L, 46), xytext=(0, 46), arrowprops=dict(arrowstyle="<->"))
    a1.text(p.L / 2, 48, f"L = {p.L:.0f} mm", ha="center", fontsize=9)
    a1.set_xlim(p.x_trasero - 8, p.L + 20); a1.set_ylim(-55, 55); a1.set_aspect("equal")
    a1.set_title(f"{p.nombre} - vista superior (relleno: altura de la cara; punteado: piezas nominales, MEDIR)")
    a1.set_xlabel("x (mm, adelante)"); a1.set_ylabel("y (mm)")
    lat = np.abs(n[:, 1]) > 0.5
    pl = PolyCollection(tri[lat][:, :, [0, 2]], facecolor="#8fb3d9", edgecolor="#8fb3d9", lw=0.3)
    a2.add_collection(pl)
    a2.add_patch(Circle((0, r), r, fill=False, ec="#444", ls="--"))
    a2.add_patch(Rectangle((p.L - p.sensor_fondo / 2, p.sensor_altura_piso), p.sensor_fondo, p.sensor_grosor, fill=False, ec="#606", ls="--"))
    a2.add_patch(Rectangle((p.x_caster - 8, 0), 16, p.caster_altura, fill=False, ec="#000", ls=":"))
    a2.axhline(0, color="#000", lw=1)
    a2.text(p.L + 10, p.sensor_altura_piso, f"sensor a {p.sensor_altura_piso:.0f} mm", fontsize=8, va="bottom")
    a2.set_xlim(p.x_trasero - 8, p.L + 40); a2.set_ylim(-2, 40); a2.set_aspect("equal")
    a2.set_title("Vista lateral"); a2.set_xlabel("x (mm)"); a2.set_ylabel("z (mm)")
    fig.tight_layout(); fig.savefig(ruta, dpi=130); plt.close(fig)

def main():
    nombres = sys.argv[1:] or list(PRESETS)
    hubo_avisos = False
    for nom in nombres:
        p = PRESETS[nom]
        cuerpo, avisos, info = construir(p)
        tm = a_trimesh(cuerpo)
        assert tm.is_watertight, "malla no cerrada"
        if avisos:   # no se publica un STL que ya se sabe que no sirve
            print(f"== {nom} ==\nNO SE GENERA STL. Avisos: " + "; ".join(avisos))
            hubo_avisos = True
            continue
        tm.export(f"chasis_planB_{nom}.stl")
        vol = cuerpo.volume()
        b = tm.bounds
        masas = masa_estimada(vol, p.densidad_pla)
        lineas = [
            f"== {nom} ==",
            f"volumen sólido: {vol/1000:.1f} cm³",
            f"robot completo (con llantas y barra): {info['largo']:.1f} x {info['ancho']:.1f} mm (reglamento: 200 x 100)",
            f"pieza impresa: {b[1][0]-b[0][0]:.1f} x {b[1][1]-b[0][1]:.1f} x {b[1][2]-b[0][2]:.1f} mm",
            f"placa: z = {info['z_placa'][0]:.1f} a {info['z_placa'][1]:.1f} mm; cuello y almohadilla desde z = {info['z_f']:.1f} mm",
            f"separadores entre barra de sensores y almohadilla: {info['separador']:.1f} mm",
            f"motor: de |y| = {info['y_motor'][0]:.1f} a {info['y_motor'][1]:.1f} mm",
            "masa PLA estimada (relleno efectivo 60 / 80 / 100 %): " + " / ".join(f"{v:.1f} g" for v in masas.values()),
            "avisos: " + ("; ".join(avisos) if avisos else "ninguno"),
            "parámetros: " + ", ".join(f"{k}={v}" for k, v in asdict(p).items()),
        ]
        open(f"chasis_planB_{nom}.txt", "w").write("\n".join(lineas) + "\n")
        print("\n".join(lineas[:-1]))
        vista(tm, p, info, f"chasis_planB_{nom}.png")
        hubo_avisos |= bool(avisos)
    return 1 if hubo_avisos else 0

if __name__ == "__main__":
    sys.exit(main())

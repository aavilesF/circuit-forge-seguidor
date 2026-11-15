#!/usr/bin/env python3
"""Genera v2/docs/componentes.md a partir de v2/inventario.csv (fuente única). No editar componentes.md a mano."""
import csv, pathlib
R = pathlib.Path(__file__).resolve().parents[1]
rows = list(csv.DictReader(open(R/'inventario.csv', encoding='utf-8')))
ET = {'confirmada': 'recibida y confirmada', 'sin_confirmar': 'recepción sin confirmar', 'por_comprar': 'por comprar'}
out = ["# Componentes (V2) — GENERADO desde `v2/inventario.csv`", "",
 "No editar a mano: se cambia `v2/inventario.csv` y se corre `python3 v2/herramientas/generar_componentes.py`.",
 "Compras: ticket Electrónica Valtierra 5 nov y pedido UNIT 7 nov (detalle de precios en el BOM histórico `robot-casero/materiales/BOM.csv`).",
 "**Repuesto = comprada − usada.** *Usada* se verifica contra los esquemáticos con `v2/herramientas/validar_repo.py`.", "",
 "| Pieza | Comprada | Usada | Repuesto | Estado | Nota |", "|---|---|---|---|---|---|"]
for f in rows:
    c, u = f['comprada'], f['usada']
    rep = str(int(c)-int(u)) if c.isdigit() and u.isdigit() else '?'
    if f['recepcion'] == 'por_comprar' or u == 'n/a': rep = '—'
    out.append(f"| {f['pieza']} | {c} | {u} | {rep} | {ET[f['recepcion']]} | {f['nota']} |")
out += ["", "## Externos y mecánicos sin fila en el inventario",
 "Base de acrílico (≤ 3 mm), 2 llantas con rin (ya disponibles, M08), placa fenólica 20 × 20 cm doble cara (comprada), cloruro férrico, broca 0.8 mm, estaño, pasta, termofit (comprados).",
 "**Por comprar:** LiPo 2S, PTC, resistencias (30 en total: 12 × 220 Ω, 14 × 10 kΩ, 1 × 470 Ω, 1 × 100 Ω, 1 × 100 kΩ, 1 × 33 kΩ), brocas 1.0 / 1.3 / 3.2 mm, cable fino, alambre para vías, cartulina, vinil.", "",
 "## Pesos medidos (Alan, báscula)",
 "| Pieza | Peso | Fuente |", "|---|---|---|", "| Ventilador 4010 | 15 g | 13 nov (ficha: 16 g) |", "| Separadores M3 macho/hembra 6 y 10 mm | ≈ 1 g c/u | 13 nov |"]
(R/'docs/componentes.md').write_text("\n".join(out)+"\n", encoding='utf-8')

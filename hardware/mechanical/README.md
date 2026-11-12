# Mecánica — integración CAD del robot completo

Generado con CadQuery 2.8 por [`cad/generar_cad.py`](cad/generar_cad.py) a partir de `config/robot_maestro.yaml`
(vía `hardware/geometria.py`, la misma geometría que usa la PCB) y del STEP de la PCBA exportado por KiCad 9.
Marco del robot en mm: x hacia adelante desde el eje de ruedas, y a la izquierda, z hacia arriba desde el piso.

## Piezas fabricadas (PA12, Multi Jet Fusion)

| Pieza | Cantidad | Función | Archivos |
|---|---|---|---|
| `soporte_motor_base_izq/der` | 1 + 1 | Bloque entre la PCB y el motor; fija la altura de la PCB (cara inferior a 4.5 mm del piso) | `step/`, `stl/`, `planos/` |
| `soporte_motor_tapa_izq/der` | 1 + 1 | Tapa en U que abraza al motor; 4 tornillos M2 × 12 por lado atraviesan PCB, base y tapa | `step/`, `stl/`, `planos/` |
| `rueda_loca_carcasa` | 1 | Bajo la PCB, aloja la bola de 1/4 in; caja para la cabeza de los tornillos (nada sobresale hacia el piso) | `step/`, `stl/`, `planos/` |
| `rueda_loca_tapa` | 1 | Sobre la PCB, asiento superior de la bola; tuercas M2 encima | `step/`, `stl/`, `planos/` |

Los planos (`planos/*.png` y `.svg`) tienen tres vistas, cotas generales y la tabla de agujeros de cada pieza;
`planos/robot_conjunto` es el plano del conjunto con largo, ancho, alto y distancia eje-bola.

## Ensamble y vistas

- `step/robot_completo.step`: PCBA (de KiCad) + piezas fabricadas + piezas compradas + tornillería.
- `render/robot_*.png`: isométrica, isométrica trasera, superior, inferior, lateral y frontal (VTK, 2400 × 1800).
- Las piezas compradas sin modelo oficial en el entorno (motor + encoder Pololu, llanta, batería, bola) son modelos
  **simplificados con las medidas de su ficha**, con el prefijo `APROX_` en el ensamble. No representan detalles finos
  (engranes, terminales, cables).

## Verificaciones (validación CAD, no física)

`python3 hardware/mechanical/verificar_mecanica.py` lee `verificacion_mecanica.json` y `propiedades_masa.json` y escribe
[`VERIFICACION_MECANICA.md`](VERIFICACION_MECANICA.md):

1. interferencias entre piezas y contra la PCBA (sólidos reales de KiCad);
2. huella en la caja del reglamento (200 × 100 mm) con el límite de diseño de 192 × 92 mm;
3. partes rígidas a ≥ 2 mm del piso (salvo llantas, bola y la carcasa de la bola);
4. masa ≤ 450 g;
5. masa y CG del CAD contra los del simulador (± 3 % y ± 2 mm): `--actualizar-yaml` copia los valores del CAD al YAML
   si dejaran de coincidir, y entonces hay que volver a validar la simulación (`python3 sim/fase_final.py F`);
6. botones, conectores y LEDs fuera de la huella de la batería y de los soportes.

## Regenerar

```bash
hardware/electronics/generar_fabricacion.sh       # primero: exporta fabricacion/speed_follower_pcba.step
python3 hardware/mechanical/cad/generar_cad.py    # ≈ 2 min
python3 hardware/mechanical/verificar_mecanica.py
```

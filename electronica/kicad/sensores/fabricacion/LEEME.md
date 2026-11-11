# Fabricación casera de doble cara — placa `sensores`

Generado por `herramientas/exportar_fabricacion.py` desde `sensores.kicad_pcb`. **No editar a mano: regenerar.**

| Dato | Valor |
|---|---|
| Tamaño | 94.1 × 75.1 mm |
| Agujeros | 177 (166 con broca 0.8 mm, 8 con broca 1.0 mm, 3 con broca 3.2 mm) |
| Vías (alambre soldado por las dos caras) | **37** |
| Pistas en la cara de arriba | 1067 mm |
| Patas que se sueldan por las **dos** caras | 55 (`sensores_soldar_arriba.csv`) |
| Patas de piezas montadas abajo (se sueldan solo por arriba) | 48 |
| Conexiones sin rutear | **0** → ruteo completo |

## Archivos
- `sensores-sensores_cara_abajo_1a1.pdf`: cara de **abajo**. Imprimir en láser al **100 %**, **sin espejo**.
- `sensores-sensores_cara_arriba_1a1.pdf`: cara de **arriba**. Ya viene **en espejo**: imprimir al 100 % tal cual (no volver a invertir).
- `sensores-sensores_perforaciones.pdf`: perforaciones vistas desde arriba; "V###" = vía.
- `sensores_perforaciones.csv`: X, Y en mm desde la esquina superior izquierda vista desde arriba.

## Procedimiento
1. Cortar la placa con 5 mm de sobra. Medir la regla de 50 mm de cada hoja: si no mide 50 mm, no sirve.
2. Taladrar **solo los agujeros M3** (broca 3.2) usando el mapa.
3. Planchar la cara de abajo centrando sus dianas en los agujeros M3. Luego la de arriba, igual.
4. Atacar con cloruro férrico las dos caras (proteger la que no se ataca si se hace por turnos). Limpiar el tóner.
5. Taladrar el resto desde cualquier cara usando las marcas del centro de cada pad.
6. Vías: meter un alambre en cada una y soldarlo por las dos caras; cortar el sobrante.
7. Soldar los componentes. En `sensores_soldar_arriba.csv`, las patas marcadas "por las DOS caras" se sueldan arriba
   y abajo; las de piezas montadas abajo (sensores), solo arriba.
8. Antes de conectar nada: continuidad de cada vía con el multímetro.

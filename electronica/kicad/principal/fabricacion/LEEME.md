# Fabricación casera de doble cara — placa `principal`

Generado por `herramientas/exportar_fabricacion.py` desde `principal.kicad_pcb`. **No editar a mano: regenerar.**

| Dato | Valor |
|---|---|
| Tamaño | 90.1 × 106.1 mm |
| Agujeros | 147 (44 con broca 0.8 mm, 76 con broca 1.0 mm, 19 con broca 1.3 mm, 7 con broca 3.2 mm, 1 con broca 34.0 mm) |
| Vías (alambre soldado por las dos caras) | **30** |
| Pistas en la cara de arriba | 530 mm |
| Patas que se sueldan por las **dos** caras | 5 (`principal_soldar_arriba.csv`) |
| Patas de piezas montadas abajo (se sueldan solo por arriba) | 0 |
| Conexiones sin rutear | **0** → ruteo completo |

## Archivos
- `principal-principal_cara_abajo_1a1.pdf`: cara de **abajo**. Imprimir en láser al **100 %**, **sin espejo**.
- `principal-principal_cara_arriba_1a1.pdf`: cara de **arriba**. Ya viene **en espejo**: imprimir al 100 % tal cual (no volver a invertir).
- `principal-principal_perforaciones.pdf`: perforaciones vistas desde arriba; "V###" = vía.
- `principal_perforaciones.csv`: X, Y en mm desde la esquina superior izquierda vista desde arriba.

## Procedimiento
1. Cortar la placa con 5 mm de sobra. Medir la regla de 50 mm de cada hoja: si no mide 50 mm, no sirve.
2. Taladrar **solo los agujeros M3** (broca 3.2) usando el mapa.
3. Planchar la cara de abajo centrando sus dianas en los agujeros M3. Luego la de arriba, igual.
4. Atacar con cloruro férrico las dos caras (proteger la que no se ataca si se hace por turnos). Limpiar el tóner.
5. Taladrar el resto desde cualquier cara usando las marcas del centro de cada pad.
6. Vías: meter un alambre en cada una y soldarlo por las dos caras; cortar el sobrante.
7. Soldar los componentes. En `principal_soldar_arriba.csv`, las patas marcadas "por las DOS caras" se sueldan arriba
   y abajo; las de piezas montadas abajo (sensores), solo arriba.
8. Antes de conectar nada: continuidad de cada vía con el multímetro.

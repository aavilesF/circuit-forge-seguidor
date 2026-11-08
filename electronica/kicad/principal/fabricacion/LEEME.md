# Fabricación casera — placa `principal`

Generado por `herramientas/exportar_fabricacion.py` desde `principal.kicad_pcb`. **No editar a mano: regenerar.**

| Dato | Valor |
|---|---|
| Tamaño de la placa | 90.1 × 106.1 mm |
| Agujeros | 198 (138 con broca 0.8 mm, 33 con broca 1.0 mm, 15 con broca 1.3 mm, 11 con broca 3.2 mm, 1 con broca 34.0 mm) |
| Puentes de alambre (pistas F.Cu) | **79 puentes**, 878 mm de alambre en total (`principal_puentes.csv`) |
| Conexiones sin rutear | **44** → NO fabricar todavía |

## Archivos
- `principal-principal_cobre_1a1.pdf`: patrón de cobre. Imprimir en **láser**, al **100 %** ("tamaño real", sin "ajustar a página"),
  **sin espejo**. Antes de planchar, medir la regla: debe dar 50 mm exactos.
- `principal-principal_perforaciones.pdf`: mapa de perforaciones visto desde los **componentes**, con el número de cada agujero (H###).
- `principal_perforaciones.csv`: coordenadas en mm desde la **esquina superior izquierda** de la placa vista desde
  los componentes (X a la derecha, Y hacia abajo), diámetro de diseño y broca sugerida.

## Orientación
El cobre va en la cara de abajo (B.Cu). La hoja se pone **boca abajo** sobre el cobre: la transferencia invierte
la imagen y queda como debe verse el cobre desde abajo. Por eso se imprime sin espejo. Las marcas pequeñas en el
centro de cada pad guían la broca (se taladra desde el cobre, después del ataque).

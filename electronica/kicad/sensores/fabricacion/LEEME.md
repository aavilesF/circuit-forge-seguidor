# Fabricación casera — placa `sensores`

Generado por `herramientas/exportar_fabricacion.py` desde `sensores.kicad_pcb`. **No editar a mano: regenerar.**

| Dato | Valor |
|---|---|
| Tamaño de la placa | 94.1 × 50.1 mm |
| Agujeros | 141 (123 con broca 0.8 mm, 15 con broca 1.0 mm, 3 con broca 3.2 mm) |
| Puentes de alambre (pistas F.Cu) | **93 puentes**, 547 mm de alambre en total (`sensores_puentes.csv`) |
| Conexiones sin rutear | **9** → NO fabricar todavía |

## Archivos
- `sensores-sensores_cobre_1a1.pdf`: patrón de cobre. Imprimir en **láser**, al **100 %** ("tamaño real", sin "ajustar a página"),
  **sin espejo**. Antes de planchar, medir la regla: debe dar 50 mm exactos.
- `sensores-sensores_perforaciones.pdf`: mapa de perforaciones visto desde los **componentes**, con el número de cada agujero (H###).
- `sensores_perforaciones.csv`: coordenadas en mm desde la **esquina superior izquierda** de la placa vista desde
  los componentes (X a la derecha, Y hacia abajo), diámetro de diseño y broca sugerida.

## Orientación
El cobre va en la cara de abajo (B.Cu). La hoja se pone **boca abajo** sobre el cobre: la transferencia invierte
la imagen y queda como debe verse el cobre desde abajo. Por eso se imprime sin espejo. Las marcas pequeñas en el
centro de cada pad guían la broca (se taladra desde el cobre, después del ataque).

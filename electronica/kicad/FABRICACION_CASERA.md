# Fabricación casera de las PCB (planchado / transferencia de tóner)

Decisión de Alan (D15 y 7 nov 2026): las PCB de la competencia se hacen **en casa**, en placa fenólica de cobre liso
(FEN20X20, una cara). Este archivo explica cómo pasar del diseño de KiCad a la placa.

## Flujo
1. Claude diseña y rutea en KiCad (`principal/`, `sensores/`).
2. `python3.12 herramientas/exportar_fabricacion.py principal sensores` genera `<placa>/fabricacion/`:
   patrón de cobre 1:1 (PDF), mapa de perforaciones (PDF + CSV), lista de puentes de alambre y un `LEEME.md`.
3. Alan imprime el patrón de cobre en **impresora láser**, al **100 %** ("tamaño real"; nunca "ajustar a página"),
   **sin espejo**, y mide la regla de 50 mm que trae la hoja.
4. Pone la hoja **boca abajo** sobre el cobre limpio y la plancha; retira el papel con agua.
5. Ataque con cloruro férrico; limpia el tóner.
6. Taladra desde el lado del cobre, usando las marcas del centro de cada pad y el mapa de perforaciones.
7. Suelda los **puentes de alambre** (pistas rojas / F.Cu de KiCad, ver `<placa>_puentes.csv`) y luego los componentes.

## Por qué sin espejo
El cobre está en la cara de abajo (B.Cu). KiCad la dibuja vista desde arriba; al planchar la hoja boca abajo, la imagen
se invierte y queda como el cobre visto desde abajo, que es lo correcto. (Si algún día se usara la cara superior, esa
sí se imprimiría en espejo.)

## Reglas de diseño para planchado (ya puestas en `herramientas/generar_pcb.py`)
| Regla | Valor | Motivo |
|---|---|---|
| Ancho de pista | 0.8 mm (mínimo) | Pistas más finas se cortan al transferir o se comen con el ácido |
| Separación entre cobre | 0.5 mm | Con menos, el tóner se corre y une pistas |
| Pads redondos | 1.8 mm | Dejan anillo de cobre después de taladrar con 0.8–1.0 mm |
| Distancia al borde | 0.5 mm | — |
| Caras | **1** (B.Cu). Lo que KiCad pone en F.Cu se hace con **alambre** | Planchar dos caras alineadas es muy difícil |
| Brocas | 0.8 mm (resistencias, TCRT5000), 1.0 mm (headers, TO-220), 1.3 mm (1N5822), 3.2 mm (M3) | E08 |

Un diseño solo es fabricable en casa si además: (a) no le faltan conexiones (`unconnected_items` = 0 en el DRC) y
(b) tiene **pocos puentes** de alambre (idealmente menos de 10–15 por placa; cada uno es una soldadura doble a mano).

## Comprobaciones que hace Alan en KiCad 10
KiCad 10 es más nuevo que la versión con la que trabaja Claude (7.0.11); abre estos archivos sin problema, pero al
guardarlos los convierte al formato nuevo. **Revisar sin guardar**, o guardar una copia aparte.

**ERC (esquemáticos)**
1. Abrir `principal/principal.kicad_pro` → Editor de esquemáticos.
2. Menú *Inspeccionar → Comprobador de reglas eléctricas* → *Ejecutar ERC*.
3. Botón *Guardar…* del mismo diálogo → guardar como `principal_erc_kicad10.rpt`.
4. Repetir con `sensores/sensores.kicad_pro`.

**DRC (PCB)**
1. Abrir el Editor de PCB del mismo proyecto.
2. *Inspeccionar → Comprobador de reglas de diseño* → marcar "Rellenar zonas" y "Comprobar paridad con el esquemático" → *Ejecutar DRC*.
3. *Guardar…* → `principal_drc_kicad10.rpt` (y `sensores_drc_kicad10.rpt`).

**Qué mirar y qué mandar:** los archivos `.rpt` completos (subirlos al chat o a la carpeta del repo). Lo más importante:
cuántos `unconnected_items` (conexiones faltantes), `clearance` / `shorting_items` (pistas demasiado cerca o en corto),
`lib_footprint_issues` / `footprint` (huellas que KiCad 10 no encuentra) y errores de paridad esquema–PCB.
No hace falta corregir nada: con los reportes Claude compara contra el DRC de KiCad 7.

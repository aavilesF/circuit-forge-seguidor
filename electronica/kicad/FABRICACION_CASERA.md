# Fabricación casera de las PCB de doble cara (planchado / transferencia de tóner)

Decisiones de Alan: D15 (placa fenólica, planchado) y **D18 (11 nov 2026): PCB de doble cara**, una sola placa fenólica con
cobre arriba y abajo. No son dos placas encimadas. Este archivo explica cómo pasar del diseño de KiCad a la placa.

## Flujo
1. Claude coloca y rutea en KiCad (`principal/`, `sensores/`) con `herramientas/generar_pcb.py`.
2. `python3.12 herramientas/exportar_fabricacion.py principal sensores` genera `<placa>/fabricacion/`:
   - patrón de la **cara de abajo** (sin espejo);
   - patrón de la **cara de arriba** (ya en espejo);
   - mapa y CSV de perforaciones;
   - lista de patas que se sueldan por arriba;
   - un `LEEME.md` con los números de esa placa.
3. Alan imprime en **láser** al **100 %** ("tamaño real"; nunca "ajustar a página") y mide la regla de 50 mm de cada hoja.
4. Taladra primero los agujeros **M3**: sirven para alinear las dos caras (cada hoja trae una diana en cada M3).
5. Plancha una cara centrando sus dianas en los M3, luego la otra. Ataca con cloruro férrico y limpia el tóner.
6. Taladra el resto, mete y suelda un **alambre en cada vía** (por las dos caras) y suelda los componentes.

## Por qué una cara va en espejo y la otra no
KiCad dibuja las dos caras vistas desde arriba, y al planchar la imagen se invierte.
- **Cara de abajo (B.Cu):** se imprime tal cual. Al invertirse queda como se ve el cobre desde abajo.
- **Cara de arriba (F.Cu):** se imprime en espejo. Al invertirse queda derecha vista desde arriba. El exportador ya la entrega en espejo: **no volver a invertirla**.

## Sin metalizado: vías y soldadura por las dos caras
- **Vía:** agujero de 0.8 mm con un alambre (una pata cortada de resistencia) soldado por arriba y por abajo. El enrutador las encarece para usar pocas. Están en el CSV como "vía".
- **Pata con pista arriba:** se suelda también por arriba. El enrutador solo lo permite donde el cautín llega:
  - piezas con el cuerpo separado de la placa (resistencias, diodos, transistores): por las dos caras;
  - módulos en tira hembra, headers, botones y capacitores: **solo por abajo**, porque el cuerpo tapa la cara de arriba;
  - **TCRT5000 de la placa de sensores:** van montados **abajo**, mirando al piso, y se sueldan **por arriba**. En KiCad su huella está volteada a la cara de abajo.

## Reglas de diseño para planchado (en `herramientas/generar_pcb.py`)
| Regla | Valor | Motivo |
|---|---|---|
| Ancho de pista | 0.8 mm | Pistas más finas se cortan al transferir o se comen con el ácido |
| Separación entre cobre | 0.5 mm | Con menos, el tóner se corre y une pistas |
| Pads de componentes | 1.8 mm (2.6 mm en el 1N5822) | Dejan anillo de cobre después de taladrar |
| Vía | pad 1.8 mm, agujero 0.8 mm | Cabe un alambre de pata de resistencia |
| Distancia al borde | 0.5 mm | — |
| Brocas | 0.8 mm (resistencias, TCRT5000, vías), 1.0 mm (headers, módulos, TO-220, PTC), 1.3 mm (1N5822), 3.2 mm (M3) | E08 |

**La placa está lista para fabricar cuando:**
- el DRC no tiene conexiones faltantes (`unconnected_items` = 0) ni errores de separación;
- la lista `*_soldar_arriba.csv` no trae ninguna pata marcada "NO";
- las huellas provisionales (ver `docs/pendientes-por-confirmar.md`) ya se confirmaron.

## Verificación con KiCad 10.0.8 (hecha el 11 nov por el servidor MCP de KiCad en la PC de Alan, E04)
Los informes JSON de `kicad-cli` 10 están en `<placa>/verificacion_kicad10/`. Resumen:

| Placa | DRC: errores | Conexiones faltantes | DRC: avisos | ERC: errores | ERC: avisos |
|---|---|---|---|---|---|
| sensores | 0 | 0 | serigrafía (10), `lib_footprint_mismatch` (30: huellas estándar de KiCad 7 vs 10); paridad: 4 pines NC del mux, 3 agujeros M3 | 0 | 226 `endpoint_off_grid`, 1 `lib_symbol_issues` (Q_NPN_EBC) |
| principal | 0 | 0 | serigrafía (34), `lib_footprint_mismatch` (18, mismo motivo); paridad: 10 pines NC del ESP32 + nFAULT del DRV8833, 4 huellas mecánicas (M3 y hueco del ventilador) | 0 | 15 `endpoint_off_grid`, 3 `pin_to_pin` (bidireccional con salida de potencia: 3V3/VIN del módulo ESP32), 1 `lib_symbol_issues` (Q_NMOS_GDS) |

Los avisos son cosméticos o esperados (pines sin usar, huellas mecánicas sin símbolo, símbolos/huellas de la biblioteca de KiCad 7
que KiCad 10 compara con las suyas). Si Alan quiere repetirlo a mano: abrir el `.kicad_pro`, *Inspeccionar → ERC* en el esquemático
y *Inspeccionar → DRC* (con "paridad con el esquemático") en la PCB. KiCad 10 convierte los archivos al guardar: revisar sin guardar
o guardar una copia aparte.

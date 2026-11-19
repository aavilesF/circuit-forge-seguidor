# Prototipo de EMERGENCIA — placa perforada (19 nov 2026)

**Motivo:** las PCB por planchado no salieron bien y faltan 2 días para la competencia (21 nov). Esta es una **alternativa** de montaje rápido en placa perforada. El diseño de PCB (`v2/electronica/principal/` y `sensores/`) **sigue vigente como referencia** y no se modificó.

Solo esquemáticos (no hay PCB, ruteo ni patrones). Generados con `herramientas/emergencia_principal.py` y `emergencia_sensores.py`, a partir de los esquemas aprobados.

## Archivos
| Archivo | Qué es |
|---|---|
| `principal_emergencia.kicad_sch` / `.pdf` / `.svg` | Placa principal: alimentación, MP1584, ESP32, DRV8833, botones, conector J6 |
| `sensores_emergencia.kicad_sch` / `.pdf` / `.svg` | Barra de 8 TCRT5000 + CD74HC4067 + 2N2222, conector J1 |
| `verificacion/` | ERC de KiCad 10.0.8 |

## Cambios respecto al diseño de PCB
| Cambio | Motivo |
|---|---|
| 12 → **8 TCRT5000** (C0–C7 del mux; C8–C15 libres) | Decisión de Alan: menos soldaduras y piezas |
| Sensores en **fila recta, paso 12.7 mm** (5 agujeros), ancho total ≈ 89 mm + cuerpo ≈ 99 mm | En placa perforada la curva no es práctica; con línea de 25 mm siempre ven la línea 2 sensores |
| Sin PTC F1 → **fusible en línea externo 3 A** en el cable rojo de la batería (F2) | No se consiguió el 0ZRE0150FF1A |
| Sin ventilador (Q1 IRLZ44N, R4, R5, D1, J5, M3) | **Recomendación de Claude, pendiente de OK (EM-01)**. GPIO del ventilador queda libre |
| Sin SW4 (RESET) | El DevKit ya trae el botón EN; el pin EN queda sin conexión |
| Se conservan | MP1584 ×2, D2, C1/C2 470 µF, divisor de batería R1/R2/C3, C4/C5 de motores, mux, 2N2222, cable de 9 hilos (mismo orden que antes) |
| Mismos GPIO del ESP32 | El firmware no necesita cambiar pines (no se tocó el firmware) |

## Lista de componentes (versión de emergencia)
| Pieza | Cant. | ¿La tenemos? |
|---|---|---|
| ESP32 DevKit 30p | 1 | Sí |
| MP1584 (5.0 V y 6.0 V) | 2 | Sí (sin repuesto) |
| DRV8833 | 1 | Sí (+1 repuesto) |
| CD74HC4067 | 1 | Sí (+1) |
| TCRT5000 | 8 | Sí (14 comprados) |
| 2N2222 | 1 | Sí |
| 1N5822 (D2) | 1 | Sí (3 comprados) |
| Capacitor 470 µF 16 V | 2 | Sí |
| Capacitor 100 nF | 4 | Sí (5) |
| Pulsador START + CAL | 2 | Sí |
| Interruptor KCD1 | 1 | Sí |
| JST-RC (batería) | 1 par | Sí |
| Motores N20 + soportes, rueda loca | 2 / 1 | Sí |
| Resistencias 220 Ω | 8 | **Comprar** |
| Resistencias 10 kΩ | 9 | **Comprar** |
| Resistencias 470 Ω, 33 kΩ, 100 kΩ | 1 c/u | **Comprar** |
| Placa perforada, LiPo 2S, fusible en línea | — | **Comprar** (ver abajo) |

## Compras de emergencia
**Imprescindible**
- **Placa perforada FR4 (fibra de vidrio verde), doble cara con agujeros metalizados, pads individuales redondos (no tiras), paso 2.54 mm.** 2 piezas de 7 × 9 cm (una principal, otra se corta para la barra de sensores de ~10 × 2.5 cm). La doble cara metalizada aguanta resoldar sin que se levanten los pads.
- **LiPo 2S 7.4 V, 450–1000 mAh, ≥ 20C**, con conector JST-RC (el que ya tenemos) o con adaptador. ~30–60 g.
- **Cargador balanceador 2S** (tipo B3 / B6) si no tienen uno. No cargar una LiPo sin balanceador.
- **Resistencias**: 8 × 220 Ω, 9 × 10 kΩ, 1 × 470 Ω, 1 × 33 kΩ, 1 × 100 kΩ (1/4 W).
- Tiras de pines hembra/macho y cable fino (22–26 AWG) si no alcanzan.

**Recomendable**
- **Portafusible en línea + fusible de 3 A** (5×20 mm de vidrio o mini de navaja), en el cable rojo, entre batería y KCD1.
- Termofit, cinta de aislar, multímetro con continuidad.

**Opcional (después de la competencia)**: ventilador y su circuito, PTC, resistencias de repuesto.

## Seguridad sin fusible (si no consiguen el portafusible)
Una LiPo en corto entrega decenas de amperes: calienta cables, quema pistas y puede incendiar la batería. Antes de conectarla: (1) multímetro en continuidad entre VBAT y GND con el KCD1 encendido y apagado: debe estar **abierto**; (2) MP1584 ajustados **antes** de soldarlos (5.0 V y 6.0 V) con fuente de laboratorio o la batería por cable con pinzas; (3) primera conexión con el ESP32 y el DRV8833 **fuera** de sus zócalos; (4) nunca dejar la batería conectada sin vigilancia ni cargar sobre material inflamable.

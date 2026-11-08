# Checklist de materiales

Marca `[x]` cuando esté comprado. Precios: **V** = verificado en UNIT (31 oct 2026), **E** = estimado.
Las tiendas físicas suelen costar más que UNIT; los precios son solo referencia.

## Comprado (ticket Electrónica Valtierra 223209, 5 nov 2026, 510 MXN)

- [x] Broca 0.8 mm (×1)
- [x] Cloruro férrico (×1)
- [x] Termofit 1/8" (×1)
- [x] Conector hembra de headers (×2 de 14 MXN y ×2 de 6 MXN; modelo del segundo sin confirmar)
- [x] Pulsadores de 4 patas: 2 pequeños (START y CAL) y 1 ancho (RESET)
- [x] Diodo Schottky 1N5822 (×2)
- [x] Transistor 2N2222 (×6)
- [x] Capacitor cerámico 100 nF (×5)
- [x] Capacitor electrolítico 470 µF 16 V (×2)
- [x] Interruptor balancín (×1)
- [x] Cable 18 AWG (×3)
- [x] Tubo de soldadura (×1)
- [x] Pasta para soldar (×1)
- [x] Placa fenólica 20 × 20 (×1)
- [x] Módulo MP1584 (×2, uno de repuesto)
- [x] Módulo DRV8833 (×2, uno de repuesto)

## Comprado (pedido UNIT Electronics, 7 nov 2026: $579 + $145 de envío = $724 MXN)

- [x] 14 sensores TCRT5000 sueltos (12 + 2 de repuesto) — $112
- [x] 2 módulos 74HC4067 (1 + 1 de repuesto) — $50
- [x] 2 "Mini rueda universal 3Pi N20" — $32 (**por confirmar si son llantas de tracción o ruedas locas: P17**)
- [x] 2 soportes para motorreductor N20/N30 — $10
- [x] 1 ventilador 4010 12 V — $32 (sustituye al "motor DC para ventilador")
- [x] 2 motorreductores GA12-N20 6 V 1000 RPM — $178
- [x] 2 pares de cables JST-RC macho/hembra — $16
- [x] 3 MOSFET IRLZ44N TO-220 (1 + 2 de repuesto) — $36
- [x] 1 kit de separadores de latón M3, 120 piezas — $113
- [x] Envío Estafeta estándar — $145
- [x] ESP32 DevKit 30 pines (ya lo tenían)

**Gastado en total:** Valtierra $510 + UNIT $724 = **$1,234 MXN** (sin contar el ESP32 que ya tenían). Quedan ~$566 contra el tope de $1,800 para la LiPo y lo que sigue pendiente.

## Pendiente (prioridad alta: sin esto no hay robot)

- [ ] LiPo 2S 7.4 V, 450–500 mAh, ≥ 20C, con balanceo y conector de potencia que coincida con el JST-RC (E: ~350)

## Pendiente (prioridad media: para que ruede bien)

- [ ] 2 llantas N20 34 × 7 mm, eje en D de 3 mm (V: 22, agotadas en UNIT) — **solo si las "ruedas 3Pi" no son llantas (P17)**
- [ ] Rueda loca o patín (O02/M30) — solo si las "ruedas 3Pi" no lo son (P17)
- [ ] Resistencias 1/4 W 5 %: 12 × 330 Ω, 12 × 10 kΩ, 2 × 1 kΩ, 2 × 100 Ω, 1 × 100 kΩ, 1 × 33 kΩ y 2 × 10 kΩ de repuesto (E: ~10)
- [ ] Fusible reseteable radial de orificio pasante, 1.5 A de mantenimiento, ≥ 16 V (ej. Littelfuse RXEF160)
- [ ] Conector JST-RC par, 2 pines (V: 8)
- [ ] Cable UTP Cat5/Cat6 (~30 cm) o cable 24–26 AWG para la placa de sensores
- [ ] Cable 22–26 AWG para motores y botones
- [ ] Cautín 30–40 W, malla desoldadora y multímetro (si el equipo no los tiene)
- [ ] Tornillos M2/M3, tuercas, separadores M3 de 10–15 mm y cinchos de 100 mm

## Pendiente (para afinar, desde la semana 2)

- [ ] Cartulina blanca mate (≥ 1.2 m)
- [ ] Cinta de vinil negra de 2.5 cm (la cinta aislante común suele ser de 19 mm)

## Pendiente (ventilador y chasis, al final)

- [ ] Material del chasis: acrílico de 2–3 mm o PLA (primero confirmar con la organización)
- [ ] Cargador balanceador 2S, solo si la escuela no presta uno (V: 227)

## Verificaciones antes de armar

- [ ] Ajustar el MP1584 a 5.0 V con multímetro **antes** de conectar el ESP32
- [ ] Confirmar que los cerámicos dicen 104 (100 nF) — confirmado por el equipo
- [ ] Revisar que el conector JST-RC coincida con el conector de potencia de la LiPo
- [ ] Corte por bajo voltaje en firmware: la LiPo 2S no debe bajar de ~6.0 V

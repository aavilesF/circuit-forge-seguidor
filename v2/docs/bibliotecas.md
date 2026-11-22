# Símbolos usados
| Pieza | Símbolo | Origen | Pines verificados |
|---|---|---|---|
| ESP32 DevKit 30p | Simbolos:ESP32-DevKit-USB-C | Alan | Sí: coincide con serigrafía M03 (1 EN … 15 5V/VIN, 16 3V3 … 30 GPIO23) |
| DRV8833 módulo | Simbolos:DRV8833 | Alan | Sí; números 1–12 coinciden con la huella. El dibujo solo es estético (P-V2-02, sin cambio) |
| MP1584 módulo | Simbolos:MP1584module | Alan | Sí. IN+ = 1, IN− = 2, OUT− = 3, OUT+ = 4; huella renumbrada igual (P-V2-01 resuelto) |
| CD74HC4067 módulo | Simbolos:HC4067_BREAKOUT_BOARD | Alan | Sí, coincide con el pinout UNIT (M17 resuelto) |
| TCRT5000 | Simbolos:TCRT5000 | Alan (no hay símbolo oficial en KiCad 10); huella oficial | Sí (M20 resuelto) |
| R, C, C_Polarized, Polyfuse, Battery | Device:* | Oficial KiCad 10 | — |
| 1N5822 | Diode:1N5822 | Oficial (1 = K, 2 = A) | Sí |
| IRLZ44N | Transistor_FET:IRLZ44N | Oficial (1 G, 2 D, 3 S) | Sí, TO-220 |
| 2N2222 | Transistor_BJT:PN2222A | Oficial (1 E, 2 B, 3 C) | Sí, coincide con M25 |
| Pulsadores / KCD1 | Switch:SW_Push / SW_SPST | Oficial | — |
| Motores / ventilador | Motor:Motor_DC / Motor:Fan | Oficial | — |
| Conectores | Connector_Generic:Conn_01x02 / 01x08 | Oficial | — |
Los símbolos con "extends" (1N5822, IRLZ44N, PN2222A) se incrustaron aplanados; KiCad da un aviso `lib_symbol_mismatch` sin efecto eléctrico.

Copia de la biblioteca de Alan usada: `v2/electronica/bibliotecas/` (símbolos y huella del MP1584 corregida).

## RobotCasero.pretty (huella aprobada por Alan)
`D_DO-201AD_P20.32mm_Taladro1.3`: 1N5822 acostado, 20.32 mm entre patas, taladro 1.3 mm (Alan, 11 y 15 nov, D-V2-33/37). Pin 1 = cátodo (franja). Usada por D1 y D2 en la PCB principal.

# Símbolos usados
| Pieza | Símbolo | Origen | Pines verificados |
|---|---|---|---|
| ESP32 DevKit 30p | Simbolos:ESP32-DevKit-USB-C | Alan | Sí: coincide con serigrafía M03 (1 EN … 15 5V/VIN, 16 3V3 … 30 GPIO23) |
| DRV8833 módulo | Simbolos:DRV8833 | Alan | Nombres sí (M10); dibujo con pines invertidos (P-V2-02) |
| MP1584 módulo | Simbolos:MP1584module | Alan | Funciones sí; IN+ sin número (P-V2-01) |
| CD74HC4067 módulo | Simbolos:HC4067_BREAKOUT_BOARD | Alan | Nombres sí; orden físico pendiente (M17) |
| TCRT5000 | Simbolos:TCRT5000 | Alan (no hay oficial en KiCad 10) | Pendiente M19/M20 |
| R, C, C_Polarized, Polyfuse, Battery | Device:* | Oficial KiCad 10 | — |
| 1N5822 | Diode:1N5822 | Oficial (1 = K, 2 = A) | Sí |
| IRLZ44N | Transistor_FET:IRLZ44N | Oficial (1 G, 2 D, 3 S) | Sí, TO-220 |
| 2N2222 | Transistor_BJT:PN2222A | Oficial (1 E, 2 B, 3 C) | Sí, coincide con M25 |
| Pulsadores / KCD1 | Switch:SW_Push / SW_SPST | Oficial | — |
| Motores / ventilador | Motor:Motor_DC / Motor:Fan | Oficial | — |
| Conectores | Connector_Generic:Conn_01x02 / 01x08 | Oficial | — |
Los símbolos con "extends" (1N5822, IRLZ44N, PN2222A) se incrustaron aplanados; KiCad da un aviso `lib_symbol_mismatch` sin efecto eléctrico.

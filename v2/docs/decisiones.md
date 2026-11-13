# Decisiones vigentes (V2)
| ID | Decisión | Origen |
|---|---|---|
| D-V2-01 | Reglamento: robot ≤ 200 × 100 mm, ≤ 500 g, sin telemetría inalámbrica; arranque con pulsador | Reglas del proyecto |
| D-V2-02 | ESP32 DevKit 30 pines USB-C, DRV8833 en módulo, 2 × MP1584 (5.0 V lógica, 6.0 V motores), N20 6 V sin encoder, LiPo 2S, ventilador 4010 12 V con IRLZ44N | D02–D04 anteriores, confirmado por Alan 12 nov |
| D-V2-03 | **PCB principal y de sensores de doble cara** (una placa fenólica con cobre en ambas caras). Definitivo; requisito de la etapa 2. Optimizar tamaño | Alan, 12 nov |
| D-V2-04 | 12 TCRT5000 sueltos + CD74HC4067 en la placa de sensores; 8 hilos a la principal | D05/D16/D20 anteriores |
| D-V2-05 | Sin zumbador, sin LED extra, sin pulldown externo en nSLEEP (el chip trae 500 kΩ), sin nFAULT conectado (P13) | D19 + Alan 12 nov |
| D-V2-06 | 3 pulsadores: START (12 × 12 mm), CAL y RESET (6 × 6 mm) | Alan, 12 nov |
| D-V2-07 | Interruptor KCD1 rojo en el chasis, cableado a la PCB (18.8 × 6.7 × 16.5 mm, 25 mm con terminales) | M27 anterior |
| D-V2-08 | Fusible PTC reseteable a la entrada de batería; valor pendiente (P-V2-03) | D24 + Alan 12 nov |
| D-V2-09 | Solo símbolos oficiales de KiCad o los de `SDL V2 General/KiCAD/Librerias` aprobados por Alan | Alan, 12 nov |
| D-V2-10 | Se usa 1 rueda loca 3Pi N20 (otra de repuesto) | Alan, 12 nov |
| D-V2-11 | Eje del N20: **diámetro ≈ 2.3 mm** (entra en el rin de 2.3 mm). El "3 mm" anterior era una longitud, no diámetro. Sobresale 8.5 mm (M05) | Alan, 12 nov (cierra P19) |
| D-V2-12 | Nunca se borran IDs; los de la rama anterior quedan en sus archivos históricos | D11 |
| D-V2-13 | PTC de referencia: radial reseteable **1.5 A de mantenimiento, ≥ 16 V** (no comprado) | Alan, 12 nov |
| D-V2-14 | Botón RESET (SW4 a EN) se queda en la PCB aunque el DevKit tenga el suyo | Alan, 12 nov |
| D-V2-15 | ESP32, MP1584, DRV8833 y mux irán sobre **tira hembra** en la PCB (los módulos usan sus pines macho) para poder cambiarlos. No se dibuja en el esquema | Alan, 12 nov |
| D-V2-16 | TCRT5000: símbolo de Alan + **huella oficial de KiCad**. Pines confirmados (M20) | Alan, 12 nov |
| D-V2-17 | Fichas de UNIT valen como medida oficial hasta medir con vernier | Alan, 12 nov |
| D-V2-18 | Esquemáticos con cables reales; etiquetas solo de complemento (cable entre placas) | Alan, 12 nov |

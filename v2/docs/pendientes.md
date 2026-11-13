# Pendientes V2
| ID | Tema | ¿Bloquea el esquema? | Notas |
|---|---|---|---|
| P-V2-01 | MP1584 de la biblioteca de Alan: el pin IN+ **no tiene número** y la huella numera sus pads solo 1 y 2 | no para el esquema (KiCad 10 conecta las redes, ERC 0); **sí para la PCB** | Alan decide si se corrige el símbolo (IN+ = 1) o se cambia la huella |
| P-V2-02 | DRV8833 de la biblioteca: los pines izquierdos (EEP, IN1–IN4, ULT) tienen el punto de conexión hacia dentro del cuerpo; eléctricamente funciona pero se ve encimado | no | Corregir el símbolo con aprobación |
| P-V2-03 | Valor del PTC (1.5 A vs 2 A) | no | Ver evaluación en el informe; falta medir corriente real de motores en arranque |
| P-V2-04 | LED de los sensores desde 3V3 del DevKit (~70 mA) o desde +5V con un hilo más | no (hoy 3V3) | Decisión de Alan |
| P-V2-05 | IRLZ44N a 3.3 V de compuerta | no | Funciona con ventilador de 100 mA (ver informe) |
| P-V2-06 | ¿RESET en la PCB o basta el botón EN del DevKit? | no | Alan dijo "si no hace falta no lo pongas" y también que usa 3 botones |
| P-V2-07 | Headers macho/hembra disponibles; qué es "5030552" | no | Para PCB |
| P-V2-08 | Módulos soldados directo (sin tira hembra) | no | Ver informe |
| P-V2-09 | TCRT5000: KiCad 10 no tiene símbolo oficial (MCP: "Sensor_Proximity:TCRT5000 no existe"); se usó el de Alan | no | Confirmar orden físico A, CATH, COLL, E (M19/M20) antes de la PCB |
| P-V2-10 | Medidas de la placa de sensores | no | Etapa 2, dentro del reglamento |
| P-V2-11 | Pendientes mecánicos heredados: C01 espesor, C02 material, R01 ventilador, R03 altura rueda loca, M14/M15 LiPo | no | Etapa 3 |

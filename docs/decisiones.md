# Registro de decisiones

Aquí se anota cada decisión importante del equipo: problema, opciones, decisión, justificación y qué información obligaría a revisarla. Solo se marca como **Decidido** lo que el equipo acordó.

## Decididas

### D1. Compra de componentes
- **Decisión:** comprar todo nuevo, en línea o en tienda física de León o Irapuato, priorizando rapidez sin sacrificar estabilidad.
- **Justificación:** el equipo no tiene componentes propios aprovechables y el plazo es corto.

### D2. Repositorio
- **Decisión:** repositorio privado `circuit-forge-seguidor` en la cuenta aavilesF.

### D3. Microcontrolador: ESP32
- **Decisión:** el robot usa un ESP32 (placa de 38 pines). Confirmado por Alejandro el 30 de octubre de 2026, después de comparar con la lista de componentes del profesor (Arduino Nano, STM32 Blue Pill o ESP32 con la radio desactivada). Si Alan o Daniel no están de acuerdo, se reabre con una propuesta en `modificaciones/`.
- **Justificación:** Alejandro conoce lo básico de Arduino y del ESP32, y Alan ya hizo un seguidor con Arduino. El ESP32 es mucho más rápido que un Nano (240 MHz frente a 16 MHz) y se puede programar desde Arduino IDE. La razón de fondo la dio Alejandro al decidir; esta justificación la redactó la IA a partir de los datos del equipo.
- **Consecuencias:** todo lo conectado a sus pines trabaja a 3.3 V (P11). Hay que resolver los canales analógicos del sensor (P10). WiFi y Bluetooth deben quedar apagados en el firmware, porque el reglamento prohíbe la comunicación inalámbrica en competencia.
- **Qué lo haría revisar:** que la lectura de los sensores resulte demasiado ruidosa o lenta en pruebas.

## Registro de avance técnico (no son decisiones del equipo)

- 31 oct 2026: se creó el firmware base, el simulador y la guía de armado. Los valores `kp=0.04`, `kd=0.002` son un punto de partida salido de simulación (modelo ideal), no de pruebas con el robot.
- Hallazgo de la simulación: el **retardo entre lectura y actuación** pesa mucho más que el ruido o el tipo de sensor. Con 12 ms de retardo el error medio sube de 1.6 a 6.8 mm. Con 24 canales leídos dos veces (emisores encendidos y apagados) hay que medir el tiempo real de lectura en el ESP32 (guía de armado, etapa 6).
- En la simulación el arreglo curvo de 24 canales **no mejora** el seguimiento frente al QTR-8A en la pista de prueba. Esto no decide P10; solo dice que la elección debe basarse en disponibilidad, precio y tiempo de lectura.
- Pines asignados en `firmware/seguidor/pines.h` (propuesta; verificar con la placa real). Multiplexores CD74HC4067 para 8 y 24 canales.

## Pendientes

### P1. Entorno de firmware
- **Opciones:** Arduino IDE o PlatformIO.
- **Propuesta (no acordada):** Arduino IDE, con la matemática (posición de la línea y PID) escrita en C++ sin depender del hardware para poder probarla en computadora.
- **Avance:** el código se escribió compatible con Arduino IDE y PlatformIO (`firmware/platformio.ini`). **No se pudo compilar con el SDK real de ESP32 desde el entorno donde se escribió**; la primera compilación real es la etapa 1 de `docs/armado.md`.
- **Falta:** que el equipo decida, sobre todo Alan, que ya conoce Arduino.

### P2. Microcontrolador
- **Resuelta:** ver D3 (ESP32).

### P3. Sensor, motores, driver y batería
- **Falta:** validar la lista de `presupuesto.md` con datos de fichas técnicas.

### P4. Roles del equipo
- **Falta:** acordar quién lleva hardware, firmware y control, y presupuesto y compras.

### P5. Presupuesto total y aportaciones
- **Falta:** fijar el monto total y lo que aporta cada integrante.

### P6. Arquitectura y plan propuestos
- **Propuesta (no acordada):** ESP32, QTR-8A, TB6612FNG, motores N20 de 6 V, LiPo 2S y dos reguladores buck, con congelamiento del diseño el 15 de noviembre. Detalle en [plan.md](plan.md). Una versión anterior proponía Arduino Nano; esta la reemplaza.
- **Microcontrolador:** ya decidido, ver D3. El resto de la arquitectura sigue como propuesta.
- **Falta:** que el equipo valide cada elemento con fichas técnicas y lo apruebe.

### P7. Alimentación de los motores
- **Problema:** con la batería conectada directo a motores de 6 V, la velocidad cambia con el nivel de carga.
- **Propuesta (no acordada):** buck de 6 V para los motores y buck de 5 V para el ESP32. Con ello la velocidad deja de depender de la carga. Alternativa más barata: un solo buck de 5 V, con motores más lentos.
- **Falta:** decisión del equipo.

### P10. Canales analógicos del sensor con ESP32
- **Problema:** el QTR-8A tiene 8 salidas analógicas y en las placas de 38 pines el ADC1 normalmente solo expone unos 6 pines utilizables.
- **Opciones:** usar pines del ADC2 sin iniciar el WiFi (por confirmar y probar), cambiar a QTR-8RC (digital), usar 6 sensores, o un multiplexor analógico de 16 canales (CD74HC4067, que aparece en la lista del profesor): una sola entrada analógica del ESP32 más 4 líneas de selección. Para 24 sensores harían falta dos multiplexores. Con un multiplexor hay que comprobar el tiempo de lectura de todos los canales y que a 3.3 V funcione bien.
- **Avance:** `pines.h` implementa la opción de multiplexores (1 chip para 8 sensores, 2 para 24). Pendiente decidir el sensor y confirmar el pinout de la placa real.
- **Falta:** confirmar el pinout de la placa y decidir.

### P11. Voltaje de las entradas del ESP32
- **Regla propuesta:** todo lo conectado a pines del ESP32 funciona a 3.3 V. El QTR-8A y la lógica del TB6612FNG se alimentan a 3.3 V, no a 5 V, porque la salida analógica del sensor llega hasta su voltaje de alimentación.
- **Falta:** que Alan lo confirme con las fichas técnicas.

### P12. RPM de los motores
- **Problema:** los N20 de 70 a 100 RPM de la lista inicial son demasiado lentos (unos 0.17 m/s con rueda de 33 mm).
- **Falta:** definir la velocidad objetivo y elegir las RPM y la relación de reducción en consecuencia, comprobando el par.

### P8. Chasis impreso por un servicio de la universidad
- **Problema:** el reglamento exige chasis fabricado por los participantes.
- **Falta:** preguntar a la organización (camilo.duque@tec.mx) si ese servicio cumple la regla, antes de pagar la impresión.

### P9. Confirmación con la organización
- **Falta:** confirmar que el reglamento publicado coincide con el texto de `requisitos.md` y que la inscripción del equipo quedó aceptada.

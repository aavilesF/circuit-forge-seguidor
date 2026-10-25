# Registro de decisiones

Aquí se anota cada decisión importante del equipo: problema, opciones, decisión, justificación y qué información obligaría a revisarla. Solo se marca como **Decidido** lo que el equipo acordó.

## Decididas

### D1. Compra de componentes
- **Decisión:** comprar todo nuevo, en línea o en tienda física de León o Irapuato, priorizando rapidez sin sacrificar estabilidad.
- **Justificación:** el equipo no tiene componentes propios aprovechables y el plazo es corto.

### D2. Repositorio
- **Decisión:** repositorio privado `circuit-forge-seguidor` en la cuenta aavilesF.

## Pendientes

### P1. Entorno de firmware
- **Opciones:** Arduino IDE o PlatformIO.
- **Propuesta (no acordada):** Arduino IDE, con la matemática (posición de la línea y PID) escrita en C++ sin depender del hardware para poder probarla en computadora.
- **Falta:** que el equipo decida, sobre todo Alan, que ya conoce Arduino.

### P2. Microcontrolador
- **Opciones:** ESP32 o Arduino Nano, entre otras.
- **Falta:** decisión del equipo tras revisar fichas técnicas.

### P3. Sensor, motores, driver y batería
- **Falta:** validar la lista de `presupuesto.md` con datos de fichas técnicas.

### P4. Roles del equipo
- **Falta:** acordar quién lleva hardware, firmware y control, y presupuesto y compras.

### P5. Presupuesto total y aportaciones
- **Falta:** fijar el monto total y lo que aporta cada integrante.

### P6. Arquitectura y plan propuestos
- **Propuesta (no acordada):** ESP32, QTR-8A, TB6612FNG, motores N20 de 6 V, LiPo 2S y dos reguladores buck, con congelamiento del diseño el 15 de noviembre. Detalle en [plan.md](plan.md). Una versión anterior proponía Arduino Nano; esta la reemplaza.
- **Propuesta de microcontrolador:** la segunda propuesta usa ESP32 (con ello P2 pasa de "ESP32 o Nano" a "ESP32 propuesto"). Falta confirmar si el equipo lo decidió, sobre todo con Alan.
- **Falta:** que el equipo valide cada elemento con fichas técnicas y lo apruebe.

### P7. Alimentación de los motores
- **Problema:** con la batería conectada directo a motores de 6 V, la velocidad cambia con el nivel de carga.
- **Propuesta (no acordada):** buck de 6 V para los motores y buck de 5 V para el ESP32. Con ello la velocidad deja de depender de la carga. Alternativa más barata: un solo buck de 5 V, con motores más lentos.
- **Falta:** decisión del equipo.

### P10. Canales analógicos del sensor con ESP32
- **Problema:** el QTR-8A tiene 8 salidas analógicas y en las placas de 38 pines el ADC1 normalmente solo expone unos 6 pines utilizables.
- **Opciones:** usar pines del ADC2 sin iniciar el WiFi (por confirmar y probar), cambiar a QTR-8RC (digital) o usar 6 sensores.
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

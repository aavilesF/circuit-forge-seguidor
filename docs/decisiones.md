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
- **Propuesta (no acordada):** Arduino Nano clásico, QTR-8A, TB6612FNG, motores N20 de 6 V y LiPo 2S, con congelamiento del diseño el 15 de noviembre. Detalle en [plan.md](plan.md).
- **Propuesta de microcontrolador:** reemplaza la duda ESP32 o Nano de P2 por una recomendación de Nano, a validar con Alan.
- **Falta:** que el equipo valide cada elemento con fichas técnicas y lo apruebe.

### P7. Alimentación de los motores
- **Problema:** con la batería conectada directo a motores de 6 V, la velocidad cambia con el nivel de carga.
- **Opciones:** limitar el PWM y cargar completa la batería antes de cada intento, o regular a 6 V.
- **Falta:** decisión del equipo.

### P8. Chasis impreso por un servicio de la universidad
- **Problema:** el reglamento exige chasis fabricado por los participantes.
- **Falta:** preguntar a la organización (camilo.duque@tec.mx) si ese servicio cumple la regla, antes de pagar la impresión.

### P9. Confirmación con la organización
- **Falta:** confirmar que el reglamento publicado coincide con el texto de `requisitos.md` y que la inscripción del equipo quedó aceptada.

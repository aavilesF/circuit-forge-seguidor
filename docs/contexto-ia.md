# Contexto del proyecto para IAs y compañeros

Resumen para que cualquier persona o IA que trabaje en este proyecto parta del mismo contexto. **Última actualización: 28 de octubre de 2026.** Quien cambie una decisión, un dato o el estado de una compra debe actualizar este archivo y `decisiones.md` en el mismo commit.

Evento: sábado 21 de noviembre de 2026, Robolympics RMX2026, Tec de Monterrey Campus León.

Los detalles viven en los demás archivos: [README](../README.md), [requisitos](requisitos.md), [plan](plan.md), [presupuesto](presupuesto.md) y [decisiones](decisiones.md). El texto completo del reglamento no está en el repositorio; el resumen está en `requisitos.md`.

---

## 0. Cómo usar este archivo

### Prompt de arranque para pegar en tu IA

> Eres mi colaborador técnico en el proyecto de robot seguidor de línea del equipo Circuit Forge para Robolympics RMX2026. Lee `docs/contexto-ia.md` y los demás archivos de `docs/` y el README del repositorio (si no puedes leerlos, te los pego). Úsalos como única fuente de contexto: distingue siempre entre lo CONFIRMADO, lo PROPUESTO (sin aprobar) y lo PENDIENTE; no inventes precios, existencias, resultados de pruebas ni decisiones del equipo; no repitas los "Errores conocidos" de la sección 4; explícame la matemática en lugar de solo darme código; y si algo parece desactualizado o contradictorio, dímelo antes de actuar. Empieza resumiéndome en 10 líneas lo que entendiste y qué dudas te quedan.

### Reglas para cualquier IA que use este contexto
1. **Fuente de verdad:** el repositorio de GitHub. Si algo de aquí contradice a un archivo más reciente de `docs/`, manda el archivo más reciente.
2. **Prioridad entre fuentes:** (1) el reglamento oficial y la convocatoria, (2) las secciones 2 y 3 de este archivo, (3) el resto del repositorio.
3. **Nada se da por decidido** hasta que esté marcado "Decidido" en `decisiones.md` o el equipo lo confirme por escrito.
4. **Ningún precio, existencia o ficha técnica se da por verificado** salvo que se haya comprobado en la página de la tienda o del fabricante. No presentes cifras de memoria como hechos.
5. **No afirmes que algo funciona sin evidencia** (medición, foto o registro de prueba).
6. No edites `README.md` ni `docs/` directamente. Las propuestas de cambio se escriben como archivo nuevo en `modificaciones/` con su plantilla; quien administra el repositorio (hoy Alejandro) integra lo que el equipo acepte. Nunca marques una propuesta como aceptada.

---

## 1. Resumen

El equipo Circuit Forge (tres integrantes) construirá un robot seguidor de línea autónomo para la categoría Seguidores de línea de Robolympics RMX2026. Meta: de preferencia ganar; mínimo aceptable, completar la pista sin salirse. Buscan un equilibrio medio-alto entre precisión de sensores y velocidad. Alejandro quiere aprender y poder defender la matemática y el control, no solo recibir código. El plazo es corto y la mayoría del equipo no tiene experiencia en robótica, por lo que la prioridad es un robot lento pero consistente primero, y subir velocidad solo con evidencia.

## 2. Datos CONFIRMADOS

### Evento (convocatoria oficial: https://profcduquetec.github.io/robolympics/pages/convocatoria.html)
- Fecha: **sábado 21 de noviembre de 2026**, 8:00 a 16:00 h, Tec de Monterrey Campus León. (Un contexto inicial del proyecto decía 23 de noviembre: era incorrecto.)
- Equipos de hasta 3 competidores y 1 robot.
- Registro en línea hasta el 17 de noviembre de 2026, 6:00 pm; confirmación por correo el 18 de noviembre. El mismo texto menciona también el 2 de noviembre como fecha de registro. El equipo dice que **ya se inscribió**; no hay evidencia en el repositorio de que hayan recibido confirmación.
- Donación obligatoria: alimentos (arroz, lenteja, soya, frijol) por **$300 MXN por robot**, se entrega el 21 de noviembre al registrarse.
- Premio en especie a los 3 primeros lugares; reconocimiento digital para todos. Contacto: camilo.duque@tec.mx.
- Rareza a aclarar con la organización: la convocatoria describe un torneo "de robot sumo" y trae una nota de que se adaptó de la edición 2025 con fechas desplazadas un día. Hay que confirmar que el reglamento de seguidores publicado (https://profcduquetec.github.io/robolympics/pages/reglamento-seguidor-linea.html) coincide con el texto usado en `requisitos.md`. Ese enlace NO se ha revisado.

### Reglamento (resumen completo en `requisitos.md`). Puntos clave
- Pista: MDF con fórmica blanca mate 1.22 x 2.44 m; línea de vinil negro de 2.5 cm; circuito cerrado sin cruces; curvas menores a 90° y radio mayor a 15 cm (puede haber secciones en "U"); discontinuidades de hasta 5 mm; separación mínima entre líneas de 20 cm. El circuito se conoce el mismo día.
- Robot: máximo 20 cm x 10 cm, sin límite de altura, **500 g en todo momento** (descalificación sin apelación). Chasis fabricado por los participantes; prohibidos kits comerciales. Totalmente autónomo; **prohibida la comunicación inalámbrica durante la competencia** (telemetría incluida). Debe funcionar con cualquier iluminación. Arranque con pulsador o interruptor cuando el referee lo autorice; nadie lo toca después.
- Fase eliminatoria: 3 intentos, se suman los tiempos, pasan los 2 mejores de cada grupo. Máximo 5 minutos por intento. Perder la pista después del primer metro = 5 minutos. Dentro del primer metro se puede reiniciar una sola vez (20 s extra). Calibración y colocación: 15 s. Homologación de peso y medidas antes de cada intento.
- Fase final: llaves de un solo intento, dos robots en sentidos contrarios; gana quien alcance al otro con contacto evidente, complete la vuelta primero sin perder la pista, o siga en pista si el otro la pierde.
- Las reglas pueden modificarse hasta el 18 de noviembre y se avisan por correo.

### Equipo
- Nombre: **Circuit Forge**. Integrantes: Alejandro Avilés Flores, Alan Uzuel Vargas Zavala, Daniel Navarro Robledo.
- **Roles no definidos.**
- Alejandro y Daniel no tienen experiencia en robótica. Alan tiene título técnico de preparatoria en mecatrónica e hizo una vez un seguidor de línea muy simple, con ayuda de ChatGPT según él. Alan sí ha programado robots; Alejandro no.
- Alejandro estudia Ingeniería de Software y Sistemas Computacionales; sabe lo básico de Arduino, soldadura y ESP32, y puede hacer todo el código y la matemática con ayuda de IA.
- Tiempo disponible: unas 3 a 6 horas por semana por persona, o más (pendiente de precisar).
- Hardware: **no tienen nada** (ni microcontrolador, ni motores, ni sensores, ni baterías). Hay cautines.
- No tienen pista de práctica: hay que construirla.
- Chasis: no tienen impresión 3D ni corte láser, pero en la universidad venden ese servicio.
- Presupuesto: sin definir; estimado de $600 a $1,000 MXN por persona, o más.
- Compras: todo nuevo, en línea o en tienda física de León o Irapuato; prefieren México pero consideran importar; quieren rapidez sin perder estabilidad.
- Disposición: dispuestos a una solución avanzada y a hacer cualquier tarea (soldar, imprimir, programar).
- Entorno de firmware: sin definir.

### Repositorio
- Existe, privado, cuenta aavilesF. Alan y Daniel **todavía no figuran como colaboradores** (no se ha confirmado que se les haya invitado).
- Contiene `README.md`, `.gitignore` (parece plantilla de C++, no revisado a fondo) y `docs/` con `requisitos.md`, `presupuesto.md`, `decisiones.md` y `plan.md`. Ver cada archivo en el repositorio.
- Los commits aparecen con autor "Claude" (noreply@anthropic.com).

## 3. Estado de las propuestas (NINGUNA está aprobada por el equipo)

| Tema | Propuesta actual | Estado |
|---|---|---|
| Microcontrolador | ESP32 de 38 pines | **Decidido** (D3, confirmado por Alejandro el 30 de octubre) |
| Sensor | QTR-8A de 8 canales, 1 + 1 de repuesto | Propuesto. Problema de canales ADC abierto (P10) |
| Driver | TB6612FNG, 1 + 1 de repuesto | Propuesto |
| Motores | N20 de 6 V con engranes metálicos, 2 + 1 de repuesto | Propuesto. Las RPM de la lista inicial (70 a 100) son demasiado lentas; sin elegir (P12) |
| Alimentación | LiPo 2S + buck de 6 V (motores) + buck de 5 V (ESP32); sensor y lógica del driver a 3.3 V | Propuesto |
| Chasis | Prototipo en cartón o acrílico; impresión 3D al congelar geometría | Propuesto. Falta confirmar con la organización si un servicio universitario cumple "fabricado por los participantes" |
| Firmware | Arduino IDE; matemática (posición y PID) en C++ puro, probada con `g++` en computadora | Propuesto, no acordado |
| Plan | 4 semanas, congelar diseño el 15 de noviembre | Propuesto |
| Herramientas | Multímetro (imprescindible) y báscula de 1 g | Propuesto |
| Presupuesto | Total estimado $4,002.79 MXN (unos $1,334 por persona), con cifras sin verificar y sin envíos | Sin aprobar; supera el rango de $600 a $1,000 por persona |

Decidido: comprar todo nuevo (en línea o León/Irapuato), usar el repositorio privado `circuit-forge-seguidor` y usar un ESP32 como microcontrolador. Nada más.

### Calendario (fechas desde hoy)
- Al 28 de octubre: la fecha sugerida para hacer el pedido (martes 27 oct) ya pasó; no hay registro de si se pidió algo.
- 2 nov: fecha de registro mencionada en la convocatoria. 
- 8 nov: sin cambios de hardware (regla propuesta).
- 15 nov: congelar firmware y geometría (regla propuesta).
- 17 nov, 6:00 pm: cierre del formulario de registro. 18 nov: confirmación por correo y fecha tope de cambios al reglamento.
- 21 nov: competencia y entrega de la donación.
- Semanas del plan propuesto: 1 (23 a 29 oct), 2 (30 oct a 5 nov), 3 (6 a 12 nov), 4 (13 a 19 nov).

## 4. Errores conocidos de IAs anteriores (no repetirlos)

1. Un contexto inicial del proyecto decía que la competencia era el 23 de noviembre. Lo correcto es el 21.
2. Una propuesta alimentaba el QTR-8A y la lógica del TB6612 a 5 V mientras usaba un ESP32. Las entradas del ESP32 admiten 3.3 V; la salida analógica del QTR-8A llega hasta su voltaje de alimentación. Todo lo que toque pines del ESP32 va a 3.3 V.
3. Una propuesta daba por hecho que el ADC1 del ESP32 ofrece 8 canales analógicos. En placas de 38 pines normalmente solo salen unos 6 (GPIO 32, 33, 34, 35, 36, 39). Confirmar el pinout de la placa real. Alternativas: pines del ADC2 sin iniciar el WiFi (por confirmar y probar), QTR-8RC digital, o 6 sensores.
4. Una lista incluía motores N20 de 70 a 100 RPM. Con rueda de 33 mm dan unos 0.17 m/s sin carga: demasiado lentos. v = pi x D x RPM / 60; 300 RPM dan unos 0.52 m/s y 600 RPM unos 1.04 m/s.
5. Un presupuesto sumaba $4,689 con un bloque de componentes anotado en $2,200 cuando sus renglones suman $1,513.79. El total correcto con esas cifras es $4,002.79.
6. Una IA marcó precios como "Verificado" sin dar enlaces. **Ninguno está verificado.**
7. Se afirmó que el paso entre sensores del QTR-8A es unos 6 mm; otra estimación indicaba unos 9.5 mm. Ninguna cifra está confirmada: revisar la ficha de Pololu.
8. Se dijo que el peso era un riesgo de descalificación. Con estas piezas se estima entre 150 y 250 g (sin medir), muy por debajo de 500 g. Pesar sigue siendo buena práctica.
9. Una propuesta asignaba tareas y una reunión a Alan y Daniel que ellos no han aceptado.

## 5. Preguntas abiertas
- ¿Qué placa ESP32 exacta se compra y con qué chip USB (CP2102 o CH340)? ¿Alan y Daniel están de acuerdo con el ESP32?
- ¿Ya se hizo algún pedido? ¿Quién compra, en qué tiendas y con qué presupuesto total y aportaciones?
- ¿Llegó la confirmación de inscripción? ¿El reglamento publicado coincide con `requisitos.md`? ¿Un chasis impreso por el servicio de la universidad cumple la regla? (Pendiente de escribir a camilo.duque@tec.mx.)
- ¿Cuál es la velocidad objetivo, y por tanto las RPM y la reducción de los motores?
- ¿Cómo se resuelven los canales analógicos del sensor (P10)?
- ¿Dónde se arma y se guarda la pista? ¿Quién la construye?
- ¿Se invitó a Alan y Daniel al repositorio? ¿Qué roles aceptan?
- ¿Hay multímetro y báscula disponibles?

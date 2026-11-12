# Matriz de reglamento — Speed Follower RMX2026

**Fuente:** [Reglamento Seguidores de línea RMX2026](https://profcduquetec.github.io/robolympics/pages/reglamento-seguidor-linea.html) y [Convocatoria RMX2026](https://profcduquetec.github.io/robolympics/pages/convocatoria.html), leídos el 31 oct 2026 (22:55 h, hora de México). El reglamento se cargó en el navegador porque su texto se genera con JavaScript.
**Vigencia:** el comité de jueces puede modificar las reglas a más tardar el **18 nov 2026**, y los cambios se avisan por correo a los equipos registrados (sección Transitorios). Esta matriz debe revisarse ese día.
**Aviso:** el sitio está en GitHub Pages (`profcduquetec.github.io`), no en un dominio del Tec. Se toma como oficial porque la convocatoria enlaza al reglamento y el contacto es `camilo.duque@tec.mx`, pero conviene confirmarlo.

Las reglas están **parafraseadas**; la columna "Sección" indica dónde está el texto original.
Estados: **Cumple (diseño)** = el diseño lo satisface en papel · **Verificar** = requiere medición o prueba física · **Consultar** = el texto es ambiguo y hay que preguntar a los organizadores · **Riesgo** = el diseño anterior podía incumplir.

## 1. Robot

| ID | Regla (paráfrasis) | Sección | Requisito de diseño derivado | Parámetro maestro (`config/robot_maestro.yaml`) | Cómo se verifica | Estado |
|---|---|---|---|---|---|---|
| R01 | El robot debe caber en una caja de 20 × 10 cm (largo × ancho), sin límite de altura | Especificaciones de los robots | Huella total ≤ 192 × 92 mm, incluidas llantas, barra, tornillos y cables (4 mm de holgura por lado) | `reglamento.largo_max`, `ancho_max`, `diseno.margen_caja` | Caja de prueba de 200 × 100 mm impresa o de cartón, en cada versión del robot | Verificar |
| R02 | No puede desplegar extensiones que rebasen las medidas una vez iniciada la contienda | Especificaciones de los robots | Nada móvil fuera del contorno: barra rígida, sin alerones ni faldones que se abran | — | Inspección | Cumple (diseño) |
| R03 | Peso máximo 500 g **en todo momento**; exceder es descalificación sin apelación | Especificaciones de los robots | Límite de diseño 450 g. La succión no debe estar activa al pesarlo: con el ventilador encendido, la báscula mediría peso + succión | `reglamento.masa_max`, `diseno.masa_limite_diseno` | Báscula de 0.1 g con batería, cables y tornillería; ventilador **apagado** hasta START | Verificar |
| R04 | Partes no provenientes de ningún kit comercial; chasis y cuerpo fabricados por los participantes; prohibido usar piezas de otros robots comerciales | Especificaciones de los robots | Chasis propio (impreso o PCB diseñada por el equipo). Módulos sueltos (sensor, driver, MCU) son componentes, no kits. **El "apoyo 3Pi" del diseño anterior es una pieza de un robot comercial (Pololu 3pi)** | BOM | Revisión de la BOM: ninguna pieza vendida como repuesto de un robot comercial | **Riesgo** (apoyo 3Pi) + Consultar (PCB fabricada por un tercero) |
| R05 | Funcionamiento totalmente autónomo | Especificaciones de los robots | Sin control remoto; el robot decide solo a partir de sus sensores | — | Revisión del firmware | Cumple (diseño) |
| R06 | Debe operar con cualquier iluminación y sonido; no se pueden pedir condiciones especiales | Especificaciones de los robots | Sensores con emisor modulado: leer con emisor encendido y apagado y restar la luz ambiente. Ningún sensor de sonido | `control` | Prueba con lámpara directa, luz solar y penumbra | Verificar |
| R07 | Sin restricción de método de control | Especificaciones de los robots | Libertad total (PD, mapeo, perfil de velocidad) | — | — | Cumple |
| R08 | Arranque con pulsador o interruptor, solo cuando el referee autoriza | Especificaciones de los robots | Botón START con antirrebote; el robot no se mueve antes de pulsarlo | — | Prueba en mesa | Cumple (diseño) |
| R09 | Tras activarlo nadie puede manipular el robot | Especificaciones de los robots | Sin ajustes durante la vuelta; toda la configuración se guarda antes | — | — | Cumple (diseño) |
| R10 | Prohibido usar comunicación inalámbrica para telemetría o control durante la competencia | Especificaciones de los robots | Radios apagadas en firmware (sin inicializar WiFi/BT; en ESP32, `WiFi.mode(WIFI_OFF)` y `btStop()`). **El texto no prohíbe tener un módulo de radio instalado**, solo usarlo | — | Revisar el firmware; opcionalmente, un MCU sin radio (STM32, Teensy) elimina la duda | Cumple (diseño) + Consultar |
| R11 | El robot no puede incluir partes que comprometan la integridad de la pista, de las personas o de sí mismo | Especificaciones de los robots | Sin aristas que rocen la fórmica; altura del chasis ≥ 2 mm; faldón de succión (si se usa) sin contacto abrasivo ni capaz de levantar el vinil | `geometria` | Recorrer una pista de vinil y revisarla | Verificar |
| R12 | Cada equipo trae sus herramientas para rearmar o reprogramar | Especificaciones de los robots | Kit de pits: cable USB, laptop con el entorno instalado, batería cargada de repuesto, tornillería y llanta de repuesto | — | Lista de pits | Pendiente |

## 2. Pista

| ID | Regla (paráfrasis) | Sección | Requisito de diseño derivado | Parámetro maestro | Estado |
|---|---|---|---|---|---|
| P01 | MDF con fórmica blanca mate de 1.22 × 2.44 m | Especificaciones de la pista | Coeficiente de fricción llanta-fórmica **desconocido**: hay que medirlo en fórmica real | `reglamento.tablero`, `traccion.mu` | Verificar |
| P02 | Línea de vinil negro de 2.5 cm, trayectoria cerrada sin cruces | Especificaciones de la pista | Paso de sensores ≤ 12.5 mm, para que siempre haya al menos 2 sensores sobre la línea | `reglamento.ancho_linea`, `control.paso_sensor` | Cumple (diseño, paso 8 mm) |
| P03 | Curvas de ángulo menor a 90° (medido desde el frente del robot) y radio mayor a 15 cm; se permiten secciones en "U" | Especificaciones de la pista | Diseñar para R = 150 mm. El cuello queda limitado por la captura de la barra (ver CALCULOS §5) | `reglamento.radio_min_linea` | Consultar: no queda claro si una U de 180° cuenta como una sola curva |
| P04 | Discontinuidades de hasta 5 mm | Especificaciones de la pista | El control mantiene la última dirección al perder la línea; a 2 m/s un hueco dura 2.5 ms | `reglamento.hueco_max` | Verificar |
| P05 | Separación entre líneas ≥ 20 cm | Especificaciones de la pista | Con barra de ≤ 92 mm, la barra no puede ver dos tramos a la vez | `reglamento.separacion_min` | Cumple (diseño) |
| P06 | Circuitos distintos y desconocidos de antemano | Especificaciones de la pista; Convocatoria | El robot no puede depender de un mapa precargado; un mapa solo puede aprenderse durante la vuelta | — | Cumple (diseño reactivo) |

## 3. Competencia

| ID | Regla (paráfrasis) | Sección | Requisito derivado | Estado |
|---|---|---|---|---|
| C01 | Eliminatoria: 3 intentos por robot; se suman los tiempos; pasan los 2 mejores de cada grupo | Fundamentos | La **constancia** vale tanto como la velocidad: un intento perdido vale 5 min | — |
| C02 | Homologación de peso y medidas antes de cada intento | Procedimientos | Pesar y medir el robot tal como compite antes de cada salida | Verificar |
| C03 | 15 s para calibrar y colocar el robot; pasarse es amonestación | Procedimientos; Violaciones | Calibración ≤ 10 s **sin que el robot se mueva solo**: cualquier movimiento antes de la señal también es amonestación. Calibración a mano o guardada en memoria | Cumple (diseño, calibración manual con tope de 10 s) |
| C04 | Frente del robot alineado con la línea de salida; no puede cruzarla antes de la orden | Procedimiento eliminatoria | Referencia física del frente (el borde de la barra) | — |
| C05 | El cronómetro para cuando el robot cruza por completo la línea de llegada | Procedimiento eliminatoria | El tiempo es de **una vuelta desde parado**: cuenta la aceleración de salida. El robot no necesita detenerse | Usado en CALCULOS |
| C06 | Si pierde la pista dentro del primer metro, puede reiniciar una vez (+20 s); en intentos posteriores se registran 5 min | Procedimiento eliminatoria | Primer metro conservador: la velocidad sube en rampa | Pendiente (firmware) |
| C07 | Perder la pista después del primer metro, rebasar 5 min o ir en sentido contrario registra 5 min | Procedimiento eliminatoria | Prioridad absoluta a no perder la línea. Recuperación corta (≤ 0.3 s) sin dar la vuelta | Cumple (diseño, firmware C2) |
| C08 | Final: 2 robots a la vez en sentidos contrarios, con las partes traseras en contacto al inicio; gana quien alcance al rival con contacto, complete la vuelta primero o siga en pista si el otro la pierde | Procedimiento fase final | Sobrevivir a un golpe trasero; la parte trasera no debe engancharse con el rival. Si nadie termina en 5 min, gana el más cercano a completar la vuelta | Verificar |
| C09 | Una pieza de más de 10 g que se separe o caiga es violación (amonestación) | Violaciones | Batería, ventilador y barra con fijación positiva (tornillo o cincho), no solo cinta | Verificar |
| C10 | Emitir humo es violación (amonestación) | Violaciones | Ningún componente sobrecargado: fusible y detección de bloqueo del motor (auditoría H17) | Pendiente |
| C11 | Un robot que no cumple las especificaciones es descalificado | Violaciones | Las reglas R01-R12 son eliminatorias | — |
| C12 | No se pueden objetar las decisiones del referee; las objeciones de reglas van al Comité de Jueces antes de terminar el juego | Objeciones | Dudas de interpretación (succión, radio, apoyo) **resueltas por escrito antes del evento** | Consultar |

## 4. Convocatoria (fechas y logística)

| ID | Dato | Fuente | Acción |
|---|---|---|---|
| V01 | Evento: sábado 21 nov 2026, 8:00-16:00, Tec de Monterrey campus León | Convocatoria §4, §9 | — |
| V02 | Registro: §6 dice "a más tardar el 2 nov"; §10 dice "hasta el 17 nov, 18:00". La propia convocatoria reconoce la doble fecha | Convocatoria §6, §10 | **Confirmar el registro antes del 2 nov** para no depender de cuál fecha aplique |
| V03 | Confirmación de inscripción: miércoles 18 nov | Convocatoria §8 | Revisar el correo |
| V04 | Donativo en especie por robot, entregado al registrarse el 21 nov | Convocatoria §9 | — |
| V05 | Equipo de hasta 3 competidores y 1 robot; solo un operador en pista (más un mecánico si el referee lo autoriza) | Convocatoria; Descripción | — |

## 5. Preguntas para los organizadores (enviar a camilo.duque@tec.mx)

1. **Succión:** ¿se permite un ventilador que genere succión contra la pista (fijo, dentro de 20 × 10 cm, sin contacto abrasivo)? En homologación, ¿se pesa el robot apagado?
2. **Radio instalado:** el ESP32 tiene WiFi/BT integrados y se desactivan por firmware. ¿Es aceptable o se exige un microcontrolador sin radio?
3. **Piezas comerciales:** ¿se aceptan módulos comerciales (barra de sensores, driver, placa de desarrollo, motorreductores, rueda loca genérica) siempre que el chasis sea propio? ¿Una PCB diseñada por el equipo y fabricada por un servicio externo cuenta como chasis "fabricado por los participantes"?
4. **Curvas:** ¿una "U" puede ser un arco continuo de 180° con radio de 15 cm, o se compone de tramos menores a 90°?
5. **Perder la pista:** ¿qué criterio usa el referee (la barra fuera de la línea, el cuerpo fuera de la línea, o que el robot deje de seguirla)?

## 6. Cambios que esta matriz obliga a hacer en el diseño anterior

- **Apoyo delantero:** sustituir el "apoyo 3Pi" (pieza de un robot comercial, R04) por una rueda loca genérica o un patín impreso por el equipo.
- **Calibración:** confirmar que no hay barrido automático con motores (C03).
- **Masa:** pesar siempre con el ventilador apagado si se adopta la succión (R03).
- **Fijaciones:** batería y barra con tornillo o cincho, no solo velcro o cinta (C09).

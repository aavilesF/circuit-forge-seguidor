# Plan de trabajo y arquitectura propuesta

**Estado:** propuesta generada con ayuda de IA (DeepSeek) y revisada con Claude. **El equipo todavía no la ha aprobado.** Nada de lo que sigue es una decisión hasta que se anote como "Decidido" en `decisiones.md`. Las tareas que mencionan a personas son sugerencias, no compromisos aceptados.

## Idea central

Cerrar esta semana una arquitectura mínima, comprar un solo conjunto de componentes con repuestos críticos, construir la pista en paralelo y llegar al 15 de noviembre con un robot lento pero consistente. La velocidad se sube solo si hay evidencia en las pruebas. Objetivo: no fallar por logística.

## Arquitectura propuesta (por validar)

| Bloque | Propuesta | Motivo | Qué hay que validar |
|---|---|---|---|
| Microcontrolador | Arduino Nano clásico (5 V, ATmega328P) | Lógica de 5 V compatible con el sensor y el driver, 8 entradas analógicas, firmware simple | Qué placa domina Alan (no está confirmado). RAM y flash justas. Si es clon, que traiga chip CH340 y tener su driver |
| Sensor | QTR-8A (8 canales analógicos) o equivalente | Resolución suficiente para una línea de 2.5 cm | Paso entre sensores y ancho total de la barra: la propuesta original decía unos 6 mm, pero la ficha de Pololu indica un paso mayor (alrededor de 9.5 mm, por confirmar). Medir que quepa en 10 cm |
| Driver | TB6612FNG (1 + 1 de repuesto) | 1.2 A continuos por canal y 3.2 A pico, lógica de 5 V | Corriente de bloqueo de los motores |
| Motores | 2 motorreductores N20 de 6 V con engranes metálicos (+2 de repuesto) | Ligeros y con par suficiente | Relación de reducción: es la decisión que más afecta la velocidad máxima. Elegirla tras estimar la velocidad objetivo |
| Batería | LiPo 2S (7.4 V), 450 a 600 mAh, con protección | Ligera, con descarga suficiente | Requiere cargador de LiPo y manejo seguro |
| Alimentación | Regulador buck a 5 V (mínimo 1 A) para la lógica. Motores conectados a la batería con el PWM limitado por software | Evita un regulador de potencia | Una 2S llega a 8.4 V cargada y baja con el uso, así que **la velocidad cambia con el nivel de batería**. Cargarla completa antes de cada intento y probar siempre en las mismas condiciones, o regular a 6 V. Vigilar la temperatura de los motores |
| Arranque | Pulsador y LED de estado | Lo exige el reglamento | Debe caber en los 15 s de calibración |
| Ruedas | Sin definir | Determinan tracción y velocidad máxima | Que encajen en el eje de 3 mm de los N20 |
| Chasis | Prototipo en cartón o acrílico primero; impresión 3D cuando se congele la geometría | Evita reimprimir | **Preguntar a la organización** si imprimir en un servicio de la universidad cumple "chasis fabricado por los participantes" |

Alternativa: ESP32 solo si Alan lo domina. No se recomienda para este plazo (pines ADC2 limitados con WiFi activo y más complejidad).

## Plan de 4 semanas

| Semana | Hito | Criterio de aceptación |
|---|---|---|
| 1 (23 a 29 oct) | Decisiones cerradas, pedido hecho, pista iniciada, firmware base probado en computadora | Lista de compra aprobada y pedido pagado. `posicion` y `pid` compilan con `g++` y pasan pruebas. MDF y vinil comprados |
| 2 (30 oct a 5 nov) | Robot armado, motores y sensores probados en banco | El robot se mueve. Las 8 lecturas responden a blanco y negro. Peso medido |
| 3 (6 a 12 nov) | Sigue la línea completa a velocidad baja y media. Pista terminada | 10 vueltas seguidas sin perder la línea, con tiempos registrados |
| 4 (13 a 19 nov) | Configuración congelada, procedimiento ensayado, repuestos listos | 20 vueltas con a lo sumo 1 pérdida. Lista de verificación de competencia |
| 20 y 21 nov | Traslado y competencia (el evento es el sábado 21) | |

Regla de congelamiento: firmware y geometría se congelan el 15 de noviembre. Del 16 al 19 solo se ajustan parámetros ya probados. Las reglas pueden cambiar hasta el 18 de noviembre: revisar el correo ese día.

Nota de peso: los topes de la propuesta original (menos de 400 g y 450 g o menos) casi no restringen, porque un robot con esta arquitectura probablemente pesa mucho menos (estimación, por medir). El límite real del reglamento es 500 g. Lo importante es medir el robot completo y revisar la tracción.

## Tareas sugeridas para esta semana (sin aceptar todavía)

- **Alejandro:** invitar a Alan y Daniel al repositorio. Escribir a camilo.duque@tec.mx para confirmar el reglamento publicado, la inscripción y la duda del chasis. Crear `firmware/seguidor/` con el esqueleto y las pruebas.
- **Alan:** validar la tabla de arquitectura con fichas técnicas, confirmar existencias en tiendas y decir qué placa domina.
- **Daniel:** armar el presupuesto con donación, pista, cargador, repuestos y envíos, y proponer aportaciones.
- **Reunión:** si el equipo puede, una reunión corta para decidir microcontrolador, sensor, driver, motores y batería, aprobar presupuesto, nombrar quién compra y fijar la fecha de pedido (la propuesta sugiere a más tardar el martes 27).

## Pista de práctica

- MDF de 1.22 x 2.44 m forrado con papel adhesivo blanco mate (más barato que fórmica).
- Línea de vinil negro de 2.5 cm. Cinta de enmascarar como guía para curvas de radio mayor a 15 cm.
- Incluir al menos una recta, una curva suave, una "U" y dos huecos de 5 mm.
- Guardarla enrollada o contra la pared, porque se usará cada semana.

## Firmware: primer entregable

Estructura propuesta, sin dependencias de Arduino en la lógica:

```
firmware/seguidor/
  seguidor.ino      pines, setup y loop
  posicion.h/.cpp   normalización y posición ponderada
  pid.h/.cpp        PID discreto con saturación y anti-windup
  motores.h/.cpp    PWM, sentido y límites
  config.h          pines y constantes
pruebas/
  test_posicion.cpp
  test_pid.cpp
  simulador.cpp     modelo diferencial simple
```

Criterios de aceptación:

- `posicion` devuelve 0 en el centro y valores con signo consistente.
- `pid` satura la salida y no acumula integral mientras satura.
- El simulador muestra que el robot converge a la línea con ganancias razonables.
- Todo compila con `g++ -std=c++17` sin `Arduino.h`.

## Reglas de decisión propuestas

1. No se compra nada sin ficha técnica y peso. Si falta el dato, se mide o se elige otra opción.
2. Repuestos obligatorios: un motor, un driver y un sensor extra.
3. Sin cambios de hardware después del 8 de noviembre.
4. Sin cambios de firmware después del 15 de noviembre, salvo parámetros.
5. Toda prueba se registra en `docs/experimentos.md`: fecha, batería, parámetros, tiempo y pérdidas de línea.
6. Criterio mínimo de éxito: 20 vueltas con a lo sumo 1 pérdida antes del 19 de noviembre.

## Lo que no se haría en esta edición

- Comprar ESP32 solo porque es más potente.
- Imprimir el chasis antes de pesar los componentes.
- Implementar encoders, odometría o control de velocidad en lazo cerrado.
- Subir la velocidad base sin 10 vueltas limpias a la velocidad anterior.
- Esperar al 18 de noviembre para confirmar el reglamento.
- Dejar la pista para la semana 3.

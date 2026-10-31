# Plan de trabajo y arquitectura propuesta

**Estado:** propuesta generada con ayuda de IA (DeepSeek) y corregida con Claude. **El equipo todavía no la ha aprobado.** Nada de lo que sigue es una decisión hasta que se anote como "Decidido" en `decisiones.md`. Las tareas que mencionan a personas son sugerencias, no compromisos aceptados.

Esta versión reemplaza la anterior (basada en Arduino Nano). El ESP32 ya está decidido (D3 en `decisiones.md`); el resto de la arquitectura sigue como propuesta.

## Idea central

Cerrar esta semana una arquitectura mínima, comprar un solo conjunto de componentes con repuestos críticos, construir la pista en paralelo y llegar al 15 de noviembre con un robot lento pero consistente. La velocidad se sube solo si hay evidencia en las pruebas. Objetivo: no fallar por logística.

## Arquitectura eléctrica propuesta (ESP32)

```
LiPo 2S 7.4 V
  |
  +-- interruptor general (y fusible)
  |
  +-- buck ajustable a 6 V (>= 2 A) ---> VM del TB6612FNG (motores N20)
  |
  +-- buck a 5 V (>= 1 A) -------------> pin 5V/VIN del ESP32
  |
  +-- el regulador de 3.3 V del ESP32 --> VCC del QTR-8A y VCC lógico del TB6612FNG
  |
  +-- tierra común para todo
```

Reglas eléctricas:

1. **Todo lo que se conecte a pines del ESP32 trabaja a 3.3 V.** Las entradas del ESP32 admiten como máximo 3.3 V (no 5 V). La salida analógica del QTR-8A llega hasta su voltaje de alimentación, así que el sensor se alimenta a 3.3 V, y por la misma razón la lógica del TB6612FNG también.
2. Medir con multímetro cada buck **antes** de conectarlo al ESP32 o al driver. La primera conexión se hace sin el ESP32 puesto.
3. Consumo del QTR-8A sobre el regulador de 3.3 V de la placa: por verificar en la ficha y medir. Si el regulador de la placa no alcanza, hay que buscar otra fuente de 3.3 V.
4. Condensadores de desacople cerca del driver y de los motores, porque el ruido de los motores afecta a las lecturas analógicas del ESP32.
5. Con 6 V regulados en los motores, la velocidad ya no depende del nivel de carga de la batería (resuelve el pendiente P7 de `decisiones.md`). Si el presupuesto aprieta, la alternativa es un solo buck de 5 V, con motores un poco más lentos.

## Componentes propuestos (por validar)

| Bloque | Propuesta | Qué hay que validar |
|---|---|---|
| Microcontrolador | ESP32 de 38 pines (ESP-WROOM-32). **Decidido (D3)** | Compatibilidad con 3.3 V y canales analógicos (ver abajo) |
| Sensor | QTR-8A (8 canales analógicos) o equivalente, 1 + 1 de repuesto | **Canales**: ver sección siguiente. Paso entre sensores y ancho de la barra (confirmar en la ficha) para que quepa en 10 cm |
| Driver | TB6612FNG, 1 + 1 de repuesto | Corriente de bloqueo de los motores frente a 1.2 A continuos por canal |
| Motores | 2 N20 de 6 V con engranes metálicos + 1 de repuesto | **RPM**: ver sección de velocidad. La opción de 70 a 100 RPM es demasiado lenta |
| Ruedas | De unos 32 a 34 mm, para eje D de 3 mm | Que encajen en el eje del motor elegido |
| Batería | LiPo 2S 7.4 V, 450 a 600 mAh, con protección | Cargador de LiPo y manejo seguro (cargar sin dejarla sola) |
| Alimentación | Buck de 6 V (>= 2 A) y buck de 5 V (>= 1 A) | Peso y tamaño de los módulos |
| Arranque | Pulsador y LED de estado | Debe caber en los 15 s de calibración |
| Herramientas | Multímetro (obligatorio) y báscula de 1 g | Ver nota de peso |
| Chasis | Prototipo en cartón o acrílico primero; impresión 3D al congelar la geometría | **Preguntar a la organización** si imprimir en un servicio de la universidad cumple "chasis fabricado por los participantes" |

### Canales analógicos del ESP32

El QTR-8A entrega 8 señales analógicas, pero en las placas de 38 pines el ADC1 normalmente solo expone 6 pines utilizables (GPIO 32, 33, 34, 35, 36 y 39). Hay que confirmar el pinout de la placa que se compre. Opciones:

- Usar también pines del ADC2. El ADC2 es incompatible con el WiFi encendido; si el firmware nunca lo inicia, debería poder usarse (evitar los GPIO 0, 2, 12 y 15, que afectan el arranque). Falta confirmarlo en la documentación de Espressif y probarlo en la placa real.
- Cambiar a un QTR-8RC (digital, por tiempo de descarga), que funciona con cualquier GPIO, con lecturas más lentas.
- Usar solo 6 sensores.
- Usar un multiplexor analógico de 16 canales (CD74HC4067): una entrada analógica del ESP32 más 4 líneas de selección. Para 24 sensores harían falta dos. Hay que medir el tiempo de lectura de todos los canales y comprobar que funcione bien a 3.3 V.

Decisión pendiente (P10 en `decisiones.md`).

### Velocidad y motores

La velocidad lineal sin carga es v = pi x D x RPM / 60. Con rueda de 33 mm:

| RPM sin carga | Velocidad aproximada |
|---|---|
| 100 | 0.17 m/s |
| 300 | 0.52 m/s |
| 600 | 1.04 m/s |

La velocidad real será menor. Con 100 RPM el robot es demasiado lento para la meta de velocidad medio-alta. Conviene fijar primero la velocidad objetivo y de ahí elegir las RPM, verificando que el par alcance en curvas. La relación de reducción es la decisión que más afecta el rendimiento.

### Peso

Estimación sin medir: entre 150 y 250 g en total, muy por debajo de los 500 g del reglamento. La báscula sirve para diseñar y para llegar a la homologación con el peso conocido, pero no es un riesgo de descalificación con estas piezas. El multímetro sí es imprescindible.

## Plan de 4 semanas

| Semana | Hito | Criterio de aceptación |
|---|---|---|
| 1 (23 a 29 oct) | Decisiones cerradas, pedido hecho, pista iniciada, firmware base probado en computadora | Lista de compra aprobada y pedido pagado. `posicion` y `pid` compilan con `g++` y pasan pruebas. MDF y vinil comprados. Multímetro y báscula comprados |
| 2 (30 oct a 5 nov) | Robot armado, motores y sensores probados en banco | El robot se mueve. Las lecturas del sensor responden a blanco y negro. Voltajes de los buck medidos. Peso medido |
| 3 (6 a 12 nov) | Sigue la línea completa a velocidad baja y media. Pista terminada | 10 vueltas seguidas sin perder la línea, con tiempos registrados |
| 4 (13 a 19 nov) | Configuración congelada, procedimiento ensayado, repuestos listos | 20 vueltas con a lo sumo 1 pérdida. Lista de verificación de competencia |
| 20 y 21 nov | Traslado y competencia (el evento es el sábado 21) | |

Regla de congelamiento: firmware y geometría se congelan el 15 de noviembre. Del 16 al 19 solo se ajustan parámetros ya probados. Las reglas pueden cambiar hasta el 18 de noviembre: revisar el correo ese día.

## Tareas sugeridas para esta semana (sin aceptar todavía)

- **Alejandro:** invitar a Alan y Daniel al repositorio. Escribir a camilo.duque@tec.mx para confirmar el reglamento publicado, la inscripción y la duda del chasis. Crear `firmware/seguidor/` con el esqueleto y las pruebas.
- **Alan:** validar la arquitectura con fichas técnicas (voltajes, corriente de bloqueo, pinout de la placa) y confirmar existencias.
- **Daniel:** armar el presupuesto con donación, pista, cargador, repuestos y envíos, y proponer aportaciones.
- **Compras:** concentrar el pedido en una o dos tiendas para reducir envíos y retrasos. La propuesta sugiere hacer el pedido a más tardar el martes 27.

## Pista de práctica

- MDF de 1.22 x 2.44 m forrado con papel adhesivo blanco mate (más barato que fórmica).
- Línea de vinil negro de 2.5 cm. Cinta de enmascarar como guía para curvas de radio mayor a 15 cm.
- Incluir al menos una recta, una curva suave, una "U" y dos huecos de 5 mm.
- Guardarla enrollada o contra la pared, porque se usará cada semana.

## Firmware: primer entregable

Estructura propuesta, sin dependencias de la plataforma en la lógica:

```
firmware/seguidor/
  seguidor.ino      estados, consola serie, calibración y guardado
  pines.h           perfil de sensor y mapa de pines (única fuente)
  parametros.h      constantes compartidas con el simulador
  posicion.h/.cpp   calibración, normalización y posición ponderada
  pid.h/.cpp        PID discreto con saturación y anti-windup
  control.h/.cpp    del error a las dos ruedas, búsqueda de línea
  hardware.h/.cpp   motores, sensores con multiplexor, botones, batería
pruebas/
  test_logica.cpp               60 pruebas con g++
  verificar_sintaxis_esp32.sh   hardware contra un stub de Arduino
simulacion/
  simular.cpp                   simulador en lazo cerrado
```

(Estructura implementada el 31 de octubre; sustituye a la propuesta inicial con `motores.*` y `config.h`.)

Criterios de aceptación:

- `posicion` devuelve 0 en el centro y valores con signo consistente.
- `pid` satura la salida y no acumula integral mientras satura.
- El simulador muestra que el robot converge a la línea con ganancias razonables.
- Todo compila con `g++ -std=c++17` sin `Arduino.h`.

Con ESP32, al inicio de `setup()` conviene dejar el WiFi y el Bluetooth apagados (el reglamento prohíbe la comunicación inalámbrica en competencia).

## Reglas de decisión propuestas

1. No se compra nada sin ficha técnica y peso. Si falta el dato, se mide o se elige otra opción.
2. Repuestos obligatorios: un motor, un driver y un sensor extra.
3. Sin cambios de hardware después del 8 de noviembre.
4. Sin cambios de firmware después del 15 de noviembre, salvo parámetros.
5. Toda prueba se registra en `docs/experimentos.md`: fecha, batería, parámetros, tiempo y pérdidas de línea.
6. Criterio mínimo de éxito: 20 vueltas con a lo sumo 1 pérdida antes del 19 de noviembre.

## Lo que no se haría en esta edición

- Imprimir el chasis antes de pesar los componentes.
- Implementar encoders, odometría o control de velocidad en lazo cerrado.
- Subir la velocidad base sin 10 vueltas limpias a la velocidad anterior.
- Esperar al 18 de noviembre para confirmar el reglamento.
- Dejar la pista para la semana 3.

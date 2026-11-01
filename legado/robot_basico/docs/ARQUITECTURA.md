# Arquitectura del robot

Estado por decisión: **Aprobada** (el equipo la decidió) · **Recomendada** (propuesta técnica, falta aprobación) · **Pendiente**.
Separación de resultados: **Cálculo** (operación verificable) · **Simulación** (`sim/`) · **Medición** (hardware real; aún no hay ninguna).

## 1. Requisitos que manda el reglamento (`[Verificado documentalmente]`, `docs/requisitos.md` y reglamento RMX2026)

| Requisito | Valor | Consecuencia de diseño |
|---|---|---|
| Huella | ≤ 20 × 10 cm, sin extensiones al correr | Barra de sensores ≤ 100 mm de ancho |
| Masa | ≤ 500 g en todo momento | Módulos ligeros; nada que pueda caerse (> 10 g caído = violación) |
| Pista | Fórmica blanca mate, vinil negro 2.5 cm, curvas < 90° con R > 15 cm, U permitidas, discontinuidades ≤ 5 mm, líneas a ≥ 20 cm, sin cruces | Sin detección de intersecciones; retener la orden en huecos |
| Arranque | Pulsador/interruptor, solo cuando el referee autoriza; mover antes = amonestación | Antirrebote y bloqueo de START |
| Comunicación | Sin inalámbrico para telemetría o control | El firmware no inicializa WiFi/BT |
| Calibración | 15 s para calibrar y colocar | Calibración ≤ 10 s y guardada en memoria |
| Pérdida de pista | Tras el primer metro = 5 min (intento perdido) | La recuperación solo sirve para excursiones pequeñas; no dar la vuelta |

## 2. Diagrama de bloques

Ver `docs/diagramas/01_bloques.png` y `02_cableado.png` (generados desde `firmware/seguidor/pines.h`).

```
LiPo 2S ─ fusible ─ interruptor ─┬─ VM TB6612FNG ─ 2× N20      (opción C2-B; hoy documentado: buck 6 V)
                                 └─ buck 5 V ─ VIN ESP32 ─ 3V3 ─ sensores, mux, VCC TB6612, botones
ESP32 ── S0..S3, SIG1/2 ── CD74HC4067 ── 8 (o 24) sensores IR       LEDON/EMISORES ── GPIO13
      ── PWMA/B, AIN, BIN, STBY ── TB6612FNG                         divisor 100k/33k ── GPIO36
```

## 3. Decisiones por bloque

### 3.1 Microcontrolador — **Aprobada** (D3, checkpoint C1)
- **Elegido:** ESP32-WROOM-32, placa DevKit de 38 pines. Fuente de precio: UNIT Electronics ($131-156 según variante).
- **Datos usados** `[Verificado documentalmente]` (Espressif ESP-IDF v4.4, ADC): ADC1 = GPIO 32-39 (36, 37, 38, 39, 32, 33, 34, 35); ADC2 falla mientras el WiFi está activo; rango sugerido con 11 dB: 150-2450 mV.
- **Variante evaluada (no se cambia sin aprobación):** ESP32-S3 DevKitC-1. Su ADC1 tiene 10 canales (GPIO1-10, Espressif v4.4.8): podría leer los 8 sensores **sin multiplexor**. Precio verificado en UNIT de una placa compatible: $191. Ventaja: lectura más simple y rápida. Riesgo: otro pinout, cambiar `pines.h` y `hardware.cpp`. **Recomendación:** quedarse con el ESP32 clásico salvo que la medición de `diag` (H11) muestre que el multiplexor es demasiado lento.

### 3.2 Sensores de línea — **Pendiente** (P10)
| Opción | Datos | Ventajas | Riesgos | Precio |
|---|---|---|---|---|
| A. "QTR-8A" de UNIT Electronics (clon TCRT5000) | 8 analógicos, 3-5 V, 100 mA, 65.7 × 16 mm, 5.5 g, detección 8-12 mm (página del vendedor) | Disponible en México (842 piezas), barato | No es Pololu: paso, polaridad y pin de emisores **sin documentar** | **$61** (verificado 31 oct) |
| B. Pololu QTR-8A original | 8 analógicos, 3.3-5 V, paso 9.525 mm, 75 × 12.7 mm, 3.09 g, 3 mm óptimo (máx. 6 mm), salida baja en blanco y alta en negro, divisores de 47 kΩ, LEDON con pull-up (bajo = LEDs apagados), puente "3.3V BYPASS" a 3.3 V (Pololu QTR-8A y guía 0J12) `[Verificado documentalmente]` | Bien documentado | Disponibilidad en México no confirmada (anuncio de Mercado Libre "no disponible") | Pendiente de cotización |
| C. Arreglo curvo de 24 | Sin modelo concreto | Más rango lateral | Sin proveedor ni ficha; 2 mux; lectura más lenta; en simulación **no mejora** el seguimiento | Pendiente |
| D. Sensores sueltos (lista del profesor) | QRE1113/ITR8307/TCRT5000 en placa propia | Geometría a la medida | Requiere PCB (nivel B, checkpoint C6) y tiempo | — |

**Recomendación:** A (disponible ya, compra 2 = 1 + repuesto), con el firmware parametrizado; B si aparece en existencia. **Por qué no más sensores:** el simulador no muestra ventaja de 24 canales en ninguna situación del reglamento y sí cuesta tiempo de lectura (el factor dominante).
Lectura: multiplexada con CD74HC4067 (TI: 2-6 V, Ron 70 Ω típ. a 4.5 V, encendido 60-300 ns entre 4.5 y 2 V, CCOM 50 pF) `[Verificado documentalmente]`.
Espera entre canales 15 µs ≈ 6 τ con τ = 47 kΩ × 50 pF ≈ 2.4 µs **(cálculo)**.

### 3.3 Driver — **Recomendada** (sin cambio): TB6612FNG
Toshiba TB6612FNG `[Verificado documentalmente]`: VM recomendado 2.5-13.5 V (máx. 15 V); VCC 2.7-5.5 V; 1.2 A promedio por canal; pico 3.2 A (pulso de 10 ms); PWM hasta 100 kHz; 0.5 Ω (alto + bajo) típ.; apagado térmico ~175 °C; STBY bajo = salidas en alta impedancia.
Compatible con 3.3 V de lógica y con 2S directo (8.4 V < 13.5 V). Módulo: $54 en UNIT (verificado).
Alternativa documentada en la página de Pololu para sus motores: MP6550 (no evaluado a fondo; pendiente).

### 3.4 Motores y transmisión — **Pendiente**
| Opción | Datos | Fuente |
|---|---|---|
| GA12-N20 6 V 1000 RPM genérico | ±10 % RPM, sin carga ≤ 0.2 A, par ≥ 0.15 kg·cm, eje D 3 mm, sección 10 × 12 mm. **Corriente de bloqueo no publicada** | UNIT, $83-90 (verificado; precio exacto por variante no leído) |
| Pololu 30:1 Micro Metal Gearmotor HP 6 V | 1000 RPM, 120 mA sin carga, **1.6 A bloqueo**, 0.57 kg·cm | pololu.com (#1093) `[Verificado documentalmente]` |
| Pololu 30:1 MP 6 V | 720 RPM, 0.67 A bloqueo, 0.33 kg·cm | pololu.com (#2364) |

Pololu recomienda operar con ≤ 25 % de la corriente de bloqueo; con 1.6 A de bloqueo, 25 % = 0.4 A, dentro del 1.2 A del TB6612. El bloqueo sostenido (1.6 A) supera el promedio del driver: evitar trabas.
**Recomendación:** genérico 6 V 1000 RPM (disponible), **midiendo la corriente de bloqueo** antes de conectarlo (protocolo F4); Pololu HP 30:1 como mejora.

**Cálculos** (supuestos explícitos: rueda Ø 33 mm, robot 0.30 kg, 60 % del peso en ruedas motrices, μ = 0.9):
- Velocidad sin carga: v = π·D·RPM/60 = π·0.033·1000/60 = **1.73 m/s**.
- Fuerza por rueda con el par mínimo del genérico: 0.15 kg·cm / 1.65 cm = 0.091 kgf = 0.89 N; dos ruedas 1.78 N → a = 1.78/0.30 = **5.9 m/s²** (sin pérdidas).
- Límite de tracción: μ·g·0.6 = 0.9·9.81·0.6 = **5.3 m/s²** → el arranque queda limitado por el agarre, no por el motor.
- Velocidad máxima en curva de R = 0.15 m: √(μ·g·R) = √(0.9·9.81·0.15) = **1.15 m/s**.
- Freno: el TB6612 tiene freno corto (IN1 = IN2 = H); con la misma fuerza, de 1.15 m/s a 0 en ≈ 0.22 s y ≈ 12 cm.

### 3.5 Batería — **Recomendada**: LiPo 2S (7.4 V nominal, 8.4 V llena)
Capacidad sugerida 300-500 mAh (ligera; un intento dura ≤ 5 min). Estimación de consumo **(cálculo con supuestos)**: lógica ~0.25 A (ESP32 sin radio + 100 mA del sensor) + motores 2 × 0.3-0.5 A en marcha → 0.9-1.3 A; 450 mAh → ~20-30 min. Cargador balanceador B3 2S/3S: $227 (UNIT, verificado). Batería: **pendiente de cotización** (UNIT no la tiene).

### 3.6 Alimentación y protección — **CHECKPOINT C2 (requiere aprobación)**

**Problema.** La arquitectura documentada usa un MP1584 para dar 6 V a los motores desde la 2S. La ficha del MP1584 (MPS, r1.1) indica: VIN 4.5-28 V, 3 A, **VIN debe superar a VOUT en más de 3 V a baja carga** y diodo bootstrap externo si VOUT/VIN > 65 %. Con 6.6-8.4 V de entrada y 6 V de salida, ambas condiciones se violan (diferencia 0.6-2.4 V; relación 71-91 %). Además, dos motores bloqueados (2 × 1.6 A Pololu HP) superan sus 3 A.

| | A. Actual (buck 6 V motores + buck 5 V lógica) | **B. Recomendada: motores directo de la batería + buck 5 V lógica** | C. Igual que B con regulador Pololu D24V10F5 para la lógica |
|---|---|---|---|
| Motores | MP1584 a 6 V fuera de su recomendación | VM = batería (≤ 8.4 V < 13.5 V del TB6612). Firmware limita el PWM a 6 V promedio: `pwm = cmd · 6 / Vbat` (ya implementado, `MOTOR_DESDE_BATERIA`) | Igual que B |
| Velocidad vs. carga | Constante si el buck regula | Constante: la compensación usa el voltaje medido | Igual |
| Lógica (5 V) | MP1584 a 5 V: margen 1.6-3.4 V, por debajo de los 3 V recomendados con batería baja | Igual que A → se **mide** en el protocolo (debe dar ≥ 4.75 V con 6.8 V de entrada) | D24V10F5: entrada mínima 5.1-5.8 V (Pololu) ✔ |
| Costo | 2 × $19 | 1 × $19 (−$19) | Pendiente de cotización (posible C4 si > $200) |
| Riesgos | Regulación de motores incierta | Motores de 6 V con picos de 8.4 V a 71 % de PWM (práctica habitual; corriente promedio equivalente a 6 V) | Disponibilidad en México |

**Recomendación: B.** Elimina la parte fuera de especificación, ahorra una pieza y el firmware ya lo soporta. **Consecuencia de no decidir:** se queda la opción A, con regulación incierta de motores.
**Para aprobar B:** poner `MOTOR_DESDE_BATERIA = true` en `pines.h`, quitar el buck de 6 V del cableado y anotar la decisión en `decisiones.md`.

Protecciones (todas las opciones): fusible reseteable en serie con el + de la batería (valor pendiente: ≥ suma de corrientes de marcha y < capacidad del conector), interruptor general, conector con polaridad única (JST/XT30) para evitar inversión — el D24V10F5 y el módulo MP1584 **no** tienen protección contra inversión —, capacitor de 100-470 µF en VM, 100 nF por módulo, tierras en estrella.

## 4. Firmware

| Módulo | Responsabilidad | Prueba en PC |
|---|---|---|
| `posicion.*` | calibración, normalización, posición ponderada, lecturas imposibles | sí |
| `pid.*` | PID discreto, saturación, anti-windup, derivada filtrada | sí |
| `control.*` | error → ruedas, freno por error, retención en huecos, búsqueda corta, compensación de batería | sí |
| `estados.*` | máquina de estados, antirrebote, monitor de batería | sí |
| `hardware.*` | ADC, multiplexor, PWM (API 2.x y 3.x del core), botones | solo sintaxis |
| `seguidor.ino` | orquestación, consola USB, NVS con versión | solo sintaxis |

**Algoritmo elegido: PD + freno proporcional al error** (Ki = 0). Comparación en simulación (`sim/resultados/comparar_*.csv`, vbase 0.6, mismos escenarios): P tiene 2.6-13 mm de error medio y sobreimpulsos de 9-33 mm; PD 0.3-1.7 mm; PID mejora 0.2-0.5 mm en curvas pero aumenta el sobreimpulso al recuperarse de desplazamientos (1.2 → 4.0 mm); el PD agresivo (Kp × 2) empeora todo. No se justifica algo más complejo (sin cruces que detectar).
Parámetros por defecto: Kp = 0.04 /mm, Kd = 0.002 s/mm, freno 30 % a 30 mm, retención 60 ms (un hueco de 5 mm dura 5 mm / v: 10 ms a 0.5 m/s; 60 ms lo cubre a cualquier velocidad ≥ 0.08 m/s), búsqueda 0.25 s. **Todos requieren calibración física.**

**Máquina de estados:** INICIO → ESPERA → CALIBRANDO → LISTO → SIGUIENDO ⇄ RECUPERANDO → PARADA; ERROR por batería al encender o sensores sin señal. START se ignora 500 ms tras arrancar. Detalle en `firmware/seguidor/estados.h`.
**Temporización:** lazo de 2 ms (500 Hz) con dt real medido; batería cada 20 ms; telemetría 1/20 ciclos; consola solo con motores apagados.

## 5. Modelo y simulación
Cinemática diferencial (v = (vD+vI)/2, ω = (vD−vI)/L), motores de primer orden (τ = 60 ms supuesto), sensores con apertura, ruido, ganancia por sensor y retardo. Detalle y límites: `docs/simulacion.md`. No modela derrape, caída de batería, zona muerta ni masa/centro de gravedad.

## 6. Preparación para PCB y CAD (nivel B, checkpoint C6 — no iniciado)
- Señales y pines: `docs/diagramas/pines.md` (19 señales). Conectores sugeridos: JST-XH 2.54 mm para sensores (VCC, GND, 8 OUT, LEDON), motores (2 × 2 pines), batería XT30 o JST-RCY, balanceo aparte.
- Corrientes: VM hasta 2 × 1.2 A continuos (pistas ≥ 1 mm); 3V3 ≤ 300 mA.
- Plano de tierra continuo bajo ADC/mux; retorno de motores separado y unido en un solo punto.
- Dimensiones: placa principal ≤ 60 × 50 mm entre ruedas; barra de sensores ≤ 100 mm.
- Mecánica futura: soporte de motores N20 (sección 10 × 12 mm), patín o caster atrás, batería sobre el eje.

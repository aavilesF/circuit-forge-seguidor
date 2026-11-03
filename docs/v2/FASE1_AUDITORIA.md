# V2 · Fase 1 — Auditoría del repositorio

Fecha: 3 nov 2026 · Rama de trabajo: `engineering/final-robot-v2`.

Tipos de dato que usa todo el trabajo V2: **Calculado** (sale de una fórmula o un script con datos declarados) ·
**Simulado** (simulador dinámico de `sim/`) · **Estimado** (orden de magnitud con base física, sin dato del fabricante) ·
**Supuesto** (escenario de estudio que se barre, no es un dato) · **Verificado documentalmente** (ficha, reglamento o fuente
citada) · **Pendiente de medición física**.

## 1. Protección del repositorio (verificado)

| Comprobación | Resultado |
|---|---|
| ¿Existía `engineering/final-robot-v2`? | **No**, ni local ni en `origin` (`git rev-parse` y `git ls-remote` vacíos) |
| Árbol de trabajo antes de crear la rama | **Limpio** (`git status --porcelain` sin líneas) |
| **Commit base** | `0714c7cd9b14e41fd440860ff9a0675a7208449b` = punta de `engineering/speed-follower` |
| Por qué esa base | Contiene todo el trabajo previo: `engineering/final-prototype` (`5abd166`) es su ancestro directo (`git merge-base` = `5abd166`) y `main` (`a12b865`) también |
| Ramas protegidas (no se tocan) | `main` = `a12b865`, `engineering/speed-follower` = `0714c7c`, `engineering/final-prototype` = `5abd166`. Sin etiquetas en el repositorio |
| Otra rama remota | `kicad-esquematico` (`c0b6321`, PCB de orificio pasante del robot básico, sale de `main`): fuera del alcance; no se toca |

## 2. Qué es V1 (estado al inicio de V2)

Speed Follower de la rama `engineering/speed-follower`: PCB-chasis de 4 capas (130 × 92 mm) con STM32G431, DRV8833 y 16
QRE1113GR en arco de R 110 mm; motores Pololu #3048 HPCB 12 V 10:1 con encoders; LiPo 2S 450 mAh; sin succión ni IMU;
112.9 g en CAD. Control C3m, v_max 0.8165 m/s, **5.81 s simulados** por vuelta (pistas sintéticas). ERC/DRC sin errores,
CAD sin interferencias, firmware compilado. **Sin ninguna validación física**: no se ha fabricado.

## 3. Clasificación de los elementos para V2

| Elemento | Ruta | Clasificación | Motivo |
|---|---|---|---|
| Matriz del reglamento | `docs/REGLAMENTO_MATRIZ.md` | **Conservar** (agregar las preguntas de §4) | Las reglas no cambian; la succión agrega dudas nuevas |
| Configuración maestra única y generadores | `config/robot_maestro.yaml`, `herramientas/` | **Conservar el patrón**; V2 tendrá su propio YAML | Evita divergencias entre simulación, firmware, BOM y PCB |
| Núcleo del simulador dinámico | `sim/nucleo.py`, `sim/simulador.py`, `sim/config.py` | **Mejorar** | Física contrastada con soluciones analíticas (`sim/pruebas/test_fisica.py`), pero la succión es una fuerza **constante** con corriente fija: falta el ventilador como sistema (curva P-Q, ranura del faldón, dinámica de arranque y caída, fallos inyectables) y la carga por rueda con la succión |
| Comparación de controladores | `sim/experimentos.py`, `sim/fase_final.py` | **Mejorar** | Hay C2/C3m/C3g/C3e; faltan PID clásico como referencia, look-ahead explícito y MPC (Fase 4) |
| Lógica del firmware en C++ puro + pruebas en PC + vectores dorados | `firmware/logica/`, `pruebas/sf/` | **Conservar** el patrón y el código de estimación de línea | El mismo código corre en PC y en el MCU; diferencias con el simulador ≤ 4.3 × 10⁻⁶ |
| Capa de hardware del STM32 | `firmware/stm32/` | **Mejorar** | Falta: mando del ventilador, tacómetro, corriente del ventilador, supervisión de fallos, IMU si se agrega |
| Barra de sensores (16 × QRE1113GR en arco, resta de luz ambiente) | `hardware/electronics/generador/diseno.py` | **Conservar el concepto**, rehacer la geometría | El radio del arco depende del cuello V2 |
| MCU STM32G431CBT6 (LQFP-48) | — | **Mejorar** (revisar encapsulado) | V1 ya usa casi todos los pines (16 ADC + VBAT, 4 PWM, 2 encoders, UART, botones, LEDs). V2 necesita además PWM o señal del ventilador, captura del tacómetro, ADC de corriente y bus para IMU o presión: probablemente un encapsulado de 64 pines de la misma familia (Fase 2) |
| Motores Pololu #3048 (10:1, 12 V, a 2S) | BOM V1 | **Reemplazar** | A 7.4 V dan ≈ 0.10 kg·cm de bloqueo por rueda (calculado de la ficha: 0.17 kg·cm a 12 V); la tabla T9 pide 0.16-0.33 kg·cm por rueda para 10-20 m/s² con 200 g. La succión vuelve útil una desaceleración que estos motores no entregan |
| Puente H DRV8833 | — | **Reemplazar o confirmar** en la Fase 2 | 1.5 A RMS por canal: depende de los motores nuevos |
| Batería Tattu 2S 450 mAh 75C | — | **Conservar como candidata** | La energía del ventilador por vuelta es < 2 mAh (T8); hay que revisar masa y corriente pico con el ventilador real |
| PCB-chasis V1 y sus piezas impresas | `hardware/electronics/kicad/`, `hardware/mechanical/` | **Reemplazar** (los archivos se conservan como referencia) | No hay cámara de succión ni lugar para el módulo del ventilador; el cuello y el arco son de V1 |
| Tubería KiCad generada (diseño → esquemático → colocación → enrutador → ERC/DRC con paridad → paquete con compuerta) | `hardware/electronics/generador/`, `generar_fabricacion.sh` | **Conservar** | Probada de punta a punta en V1 |
| Tubería CAD (CadQuery, verificación de interferencias, masa y CG contra el YAML, planos, vistas) | `hardware/mechanical/cad/`, `verificar_mecanica.py` | **Conservar** | Igual |
| Cálculos y simulaciones de V1 | `sim/resultados/*`, `docs/*` | **Conservar como evidencia** | Base de la comparación V1 contra V2 (Fase 4) |
| Diseños anteriores | `legado/` | **Conservar** sin cambios | Historia |

## 4. Riesgos de reglamento que bloquean la succión (consultar por escrito antes de la Fase 3)

| # | Pregunta | Por qué bloquea |
|---|---|---|
| 1 | ¿Se permite un ventilador que genere succión contra la pista? | Pregunta abierta desde la Fase 1 de V1 (`REGLAMENTO_MATRIZ.md` §5, C12) y sin respuesta. Sin permiso, la V2 con succión no compite |
| 2 | R03 dice "500 g **en todo momento**". ¿La succión cuenta como peso? | Para 2.0 m/s hace falta ≈ 3-5 N de succión con 200 g (T3b): el **peso aparente** con el ventilador encendido sería 518-654 g. Si se pesa encendido o si el juez lo interpreta así, el robot queda descalificado sin apelación |
| 3 | En las 3 vueltas (C01), ¿el circuito es el mismo y puede el robot recordar lo aprendido entre intentos? | Con un mapa aprendido, el robot frena antes de cada curva y la anticipación deja de ser el límite (T8b: −20 % de tiempo sin succión). Sin respuesta, se diseña como robot reactivo |
| 4 | R11: ¿un faldón a 0.3-0.5 mm de la fórmica, sin contacto, se acepta? ¿Y uno con roce ligero (cerdas, película)? | La fuerza cae a la mitad si la ranura pasa de 0.5 a 1.0 mm (T6); el faldón no puede levantar el vinil |

## 5. Uso de los archivos entregados

- **Imagen de referencia**: solo se tomó la intención general (robot alargado, frente extendido, zona central compacta).
  Ninguna medida, posición, componente ni proporción del boceto entra al diseño. Que la succión deba centrarse cerca del eje
  de las ruedas motrices **sale del cálculo** (T3b), no del boceto.
- **Modelos 3D** (`hardware/v2/referencia_succion/`): ventilador real a integrar y su montaje (base, pilar, soporte).
  Análisis en [`ANALISIS_VENTILADOR.md`](ANALISIS_VENTILADOR.md).

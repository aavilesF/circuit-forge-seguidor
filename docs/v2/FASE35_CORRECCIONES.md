# V2 · Fase 3.5 — Correcciones de la auditoría externa (commit `cd3ff42`)

Fecha: 5 nov 2026 · Rama `engineering/final-robot-v2`. Tipos: **[V]** verificado documentalmente · **[C]** calculado ·
**[E]** estimado · **[S]** supuesto · **[P]** pendiente de medición física.

| # | Hallazgo | Corrección | Evidencia |
|---|---|---|---|
| 1 | `tiempo_vuelta()` daba tiempos imposibles | Perfil de velocidad factible (atrás + adelante); T8/T8b regenerados; 11 pruebas de regresión | `sim/v2/fase1_v2.py`, `sim/v2/pruebas/test_fase1_v2.py` |
| 2 | Faldón a 0.5 mm con la succión apagada: rozaría al comprimirse las llantas | Borde inclinado calculado con la compresión (2 mm de diseño) y las cargas dinámicas: **≥ 0.5 mm en el peor caso**; variantes para 1.0 y 0.5 mm | `sim/v2/hundimiento.py`, `sim/v2/fase35.py` (T12), CAD |
| 3 | Documentación sin las reglas oficiales | `FASE1_AUDITORIA.md` §4, `FASE1_FISICA.md`, `FASE2_COMPONENTES.md` §0, `parametros_fase1.yaml` | — |
| 4 | Frenado del #5183 contra el DRV8874 | ITRIP bajado a **≈ 1.56 A**; límite de frenado de **1.5 A** y estimador térmico en el firmware | `fase35.py` (T13), esquemático |
| 5 | Datos del ventilador | 1104 ~9000 KV + ESC de 20 A; **500 Pa** de presión de cierre para todos los cálculos nuevos | `config/v2/robot_v2.yaml` → `fase35` |

## 1. Cálculo de vuelta (`sim/v2/fase1_v2.py`)

El error: en una recta, el tiempo de aceleración era (v_crucero − v)/a aunque el robot llegara **más rápido** que su crucero
(saliendo de un arco amplio), y el arco tampoco se limitaba al crucero. En el caso de prueba (recta, arco R 1 m, recta,
crucero 1.0 m/s) la versión anterior daba **1.43 s cuando el mínimo físico es 2.57 s**.

Ahora `perfil_vuelta()` arma el perfil factible sobre los topes de cada punto: pasada hacia atrás con la desaceleración de
adherencia y hacia adelante con la aceleración, desde parado. El robot **reactivo** solo puede empezar a frenar por lo que la
barra ya vio (horizonte = L, la barra va delante del eje); el robot **con mapa** conoce toda la vuelta. Si el reactivo
tuviera que frenar más de lo que la adherencia permite, la función lo marca como no factible (nunca pasó en T8/T8b).

Pruebas (`python3 -m pytest -q sim/v2/pruebas/`, 11 pasan): topes y aceleraciones respetados; recta contra la solución
analítica; el caso del error; tiempos positivos y factibles en las 4 pistas; con mapa ≤ reactivo; más crucero o más
succión nunca aumentan el tiempo; las tablas regeneradas no tienen tiempos imposibles.

Efecto en los resultados: los tiempos de T8 subieron 3-4 % (sin ventilador 3.63 → 3.76 s; máxima 2.40 → 2.49 s); el mapa
ahorra 23 % sin succión y 3 % con 4 N (antes 20 % y 3 %). **Ninguna conclusión de la Fase 1 cambia.**

## 2. Faldón: nunca toca la pista

**Modelo** (`sim/v2/hundimiento.py`): el chasis se apoya en las 2 llantas y en la bola de acero (rígida). Si las llantas se
comprimen, el chasis gira alrededor de la bola: cada punto baja (1 − x/92 mm) veces la compresión media, más el balanceo
lateral. **Detrás del eje baja más que el eje** (×1.35 en la pared trasera de la cámara); delante de la bola sube.

**Supuestos de diseño**: llanta que se comprime **2.0 mm** con la carga estática máxima (cota alta de tu estimación de
1-2 mm) [S]; succión máxima posible con 500 Pa y la cámara cerrada: **2.59 N** [C]; cargas dinámicas: aceleración de
10.5 m/s², frenado y curva al límite de adherencia y sus combinaciones al 70 % [C]. Rigidez resultante: 0.90 N/mm por llanta.

**Resultado** (T12, el CAD exporta las 3 variantes):

| Compresión de llanta de diseño | Borde trasero / delantero (sin succión) | Holgura mínima en el peor caso | Ranura media en recta | Succión real (500 Pa) | Crucero reactivo | Vuelta media reactiva / con mapa |
|---|---|---|---|---|---|---|
| **2.0 mm (por defecto, en el ensamble)** | 3.86 / 1.90 mm | **0.50 mm** | 2.14 mm | **0.28 N** | 1.31 m/s | 3.31 / 2.61 s |
| 1.0 mm | 2.18 / 1.20 mm | 0.50 mm | 1.21 mm | 0.71 N | 1.48 m/s | 2.93 / 2.39 s |
| 0.5 mm | 1.34 / 0.85 mm | 0.50 mm | 0.79 mm | 1.22 N | 1.66 m/s | 2.63 / 2.29 s |
| Referencia sin succión (156 g, L 125 mm) | — | — | — | 0 | 1.18 m/s | 3.68 s |

Todo calculado; la compresión real y la presión real están **pendientes de medición** [P].

**Verificación en el CAD** (`hardware/v2/mecanica/verificacion_mecanica.json`): se revisaron todos los vértices bajo
z = 8 mm de todas las piezas (menos llantas y bola) contra el hundimiento máximo. Holgura mínima **0.50 mm** (esquina
delantera del faldón, el punto de diseño); rueda loca 0.87 mm; cachucha 1.36 mm; sensores 2.40 mm. Los tornillos del
faldón ahora entran desde ARRIBA (autorroscantes en los refuerzos): nada sobresale por debajo del borde.

**Lo que esto significa (importante):** con una compresión de 2 mm y 500 Pa, la ranura que garantiza "nunca toca" deja
**0.28 N de succión**: el robot iría a 1.31 m/s, poco más que sin succión. La compresión real de una llanta de silicón de
32 mm con ≈ 1.8 N probablemente sea mucho menor que 2 mm, pero no la puedo verificar. **La medición más valiosa ahora es la
compresión de la llanta** (5 minutos):
1. Robot armado, apagado, sobre una superficie plana. Medir con calibrador la altura de la placa del chasis sobre el piso
   junto al eje, a cada lado.
2. Poner encima de la cámara un peso igual a la succión esperada (≈ 265 g ≈ 2.6 N con 500 Pa; más si la báscula da más).
3. Medir otra vez. La diferencia es la compresión. Imprimir la variante del faldón que corresponda
   (`faldon_camara_llanta_0p5mm.stl`, `..._1p0mm`, `..._2p0mm`) o pedirme otra con el valor medido.

Para acercarse a 2.0 m/s hacen falta las dos cosas: llantas que casi no se compriman (o llantas más duras) y más presión
que los 500 Pa conservadores (con 0.5 mm de compresión y 850 Pa, la Fase 1 da ≈ 3 N y 2.0 m/s).

## 3. Revisión térmica del frenado (T13)

Datos del motor [V, Pololu #5183 a 6 V]: 1.5 A de bloqueo, 0.15 A sin carga → resistencia del devanado ≈ 4 Ω y constante de
par en la salida ≈ 0.0164 N·m/A [C]. Térmicos del motor **estimados** (Pololu no los publica): 40 K/W y 3 J/K [E]; elevación
máxima admitida 50 K [S].

| Caso | Corriente pico | Calor | Elevación del devanado |
|---|---|---|---|
| Perfil factible (frenado limitado por la adherencia), 1.22 N y 3.1 N, 4 pistas, reactivo y con mapa | **0.95 A** (la pide la aceleración de 10.5 m/s²) | ≤ 1.43 J por vuelta | **≤ 1.4 K por ronda de 3 vueltas**; ≤ 28 K en régimen permanente (vueltas sin parar) |
| Frenar siempre con lo que deja pasar el DRV8874 con ITRIP 2.4 A (abuso) | 2.44 A | 4.9 J por vuelta (P4) | 4.1 K por ronda; **88 K en régimen permanente: quemaría el motor** |
| Lo mismo con ITRIP 1.56 A | 1.56 A | 3.0 J por vuelta (P4) | 2.7 K por ronda; 59 K en régimen permanente |

Frenar a la adherencia completa pide **≤ 1.57 A** aun con 3.1 N de succión (18.5 m/s²); más corriente solo hace patinar la
llanta y calentar el motor. Correcciones:
- **Hardware**: R26 de 10 kΩ a **4.7 kΩ** → VREF = 1.055 V → **ITRIP ≈ 1.56 A** por motor [C]. Arrancar desde parado a 6 V
  efectivos pide 1.5 A: no se recorta.
- **Firmware** (Fase 4): límite de corriente de frenado de **1.5 A** por motor (lazo con IPROPI), frenado por inversión solo
  hasta la adherencia (el control de deslizamiento usa encoders + IMU), y **estimador térmico I²t** con el modelo de primer
  orden (4 Ω, 40 K/W, 3 J/K): si la elevación estimada pasa de 40 K, baja el límite de corriente; a 50 K, error y motores
  apagados.

## 4. Ventilador

Motor brushless **1104 ~9000 KV** con **ESC comercial de 20 A** [S, usuario]; la señal del ESC sale de PB9 (TIM17_CH1:
PWM, Oneshot o DShot). Todos los cálculos de esta fase usan **ΔP₀ = 500 Pa** y Q₀ = 4.5 L/s [S] hasta la prueba de báscula
(`ANALISIS_VENTILADOR.md` §4). Con esos datos la fuerza máxima posible (cámara cerrada) es 2.59 N.

Reproducir: `python3 sim/v2/fase1_v2.py`, `python3 sim/v2/fase35.py`, `python3 -m pytest -q sim/v2/pruebas/`,
`python3 hardware/v2/mecanica/cad/generar_cad_v2.py`.

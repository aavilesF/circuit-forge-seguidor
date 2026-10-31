# Modelo virtual y simulación

Antes de comprar nada ya existe un robot virtual que corre **el mismo código de control que irá en el ESP32**
(`posicion.cpp`, `pid.cpp`, `control.cpp`). Si cambias el PID en el firmware, el simulador cambia con él.

## Cómo correrlo

```bash
pruebas/ejecutar.sh                         # 60 pruebas de la lógica (deben dar 0 fallos)
sim/ejecutar.sh                      # corrida con QTR-8A
sim/ejecutar.sh sensores=24 geom=arco paso=4 radio_arco=80   # arreglo curvo de 24
sim/ejecutar.sh vbase=0.6 kp=0.03 kd=0.001                   # cambiar cualquier parámetro
sim/ejecutar.sh modo=barrido_vbase                           # tabla de velocidades
python3 herramientas/generar_diagramas.py   # regenera todas las gráficas
```

Claves disponibles: `sensores geom paso radio_arco dist_eje L apertura ruido retardo vmax tau_m tmax offset semilla mu kp ki kd vbase freno error_ref vmin_rel u_max rueda_min retencion`.

## Las matemáticas, paso a paso

**1. Dónde está la línea (posición).** Cada sensor dice qué tan oscuro ve (0 = blanco, 1 = negro) después de calibrar.
La posición es el promedio de las posiciones de los sensores, ponderado por su oscuridad:

`pos = Σ (dᵢ · xᵢ) / Σ dᵢ`

Ejemplo con QTR-8A (sensores cada 9.525 mm) y una línea de 25 mm centrada a +10 mm. Los sensores en −4.76, +4.76, +14.29 y +23.81 mm ven 0.22, 1, 1 y 0.34 de oscuridad;
al restar el umbral de ruido (0.10) quedan 0.13, 1, 1 y 0.26:
`pos = (0.13·(−4.76) + 1·4.76 + 1·14.29 + 0.26·23.81) / (0.13+1+1+0.26) = 24.67 / 2.39 = 10.3 mm`. Real: 10 mm.

**2. Cuánto corregir (PID).** `error = pos` (positivo = la línea está a la derecha).
`u = Kp·error + Ki·∫error·dt + Kd·d(error)/dt`.
- **Kp** gira más fuerte mientras más lejos esté la línea.
- **Kd** frena el giro cuando el error ya se está cerrando (evita que el robot "se pase" y zigzaguee).
- **Ki** quita errores constantes; en seguidores rápidos casi siempre se deja en 0.
La derivada se filtra y la integral tiene anti-windup para que no explote al saturar.

**3. De corrección a ruedas.** Con velocidad base `v` y corrección `u`: rueda izquierda = `v + u`, rueda derecha = `v − u`.
Si la línea está a la derecha, la izquierda va más rápida y el robot gira a la derecha.
La velocidad base baja hasta 30 % cuando el error es grande (`freno_error`): se frena en las curvas.
Ejemplo (error = 10.3 mm, Kp = 0.04, vbase = 0.4): `v = 0.4·(1 − 0.3·10.3/30) = 0.36`, `u = 0.04·10.3 = 0.41`,
izquierda = 0.77, derecha = −0.05 (la derecha casi se detiene: giro cerrado).

**4. Cómo se mueve el robot (cinemática).** `v = (vD + vI)/2` y `ω = (vD − vI)/L`, con `L` = separación entre ruedas (75 mm nominal).
Los motores responden con retardo de primer orden (constante 60 ms nominal).

**5. Límite físico (agarre).** En una curva de radio `R` la aceleración lateral es `v²/R`. Con agarre μ ≈ 0.9 la velocidad máxima es `√(μ·g·R)`:
para R = 150 mm da ≈ **1.15 m/s**. Arriba de eso el robot derrapa, sin importar el control.

## Qué simula y qué no

Simula: pista legal de 4.4 m (cabe en 2.44 × 1.22 m, sin cruces, líneas a ≥ 20 cm, curvas de radio ≥ 15 cm, tres huecos de 5 mm, una S y dos esquinas de 90°),
sensores con apertura circular, ganancia distinta por sensor, ruido, calibración, **retardo de lectura**, motores con inercia.

**No simula:** derrape (el simulador solo avisa cuando la aceleración lateral pasa de μ·g), caída del voltaje de la batería, zona muerta de los motores,
vibración, reflejos del vinilo, iluminación, diferencia entre los dos motores, ni el tiempo real que tarda el ESP32 en leer los canales.
**Los números absolutos son optimistas.** Sirven para comparar decisiones y para tener un punto de partida, no para prometer tiempos.
Todos los parámetros del robot son nominales (`parametros.h`, `simular.cpp`): hay que sustituirlos por los reales al medir las piezas.

## Resultados (pista de prueba, kp = 0.04, kd = 0.002)

| Velocidad base | QTR-8A: tiempo / error medio | Curvo 24: tiempo / error medio | Aceleración lateral máx. |
|---|---|---|---|
| 0.20 | 14.7 s / 0.7 mm | 14.9 s / 0.7 mm | 0.1 g |
| 0.40 | 7.5 s / 1.1 mm | 7.5 s / 1.1 mm | 0.3 g |
| 0.60 | 5.2 s / 1.6 mm | 5.1 s / 1.6 mm | 0.5-0.6 g |
| 0.80 | 4.2 s / 1.8 mm | 3.9 s / 2.0 mm | 0.8 g |
| 1.00 | 4.0 s / 1.9 mm | 3.6 s / 2.1 mm | 0.9 g (límite de agarre) |

(`vmax` supuesto = 1.4 m/s con comando 1.0; hay que medirlo con el motor y la rueda reales.)

Barrido de PID (63 combinaciones por sensor): todas completan la pista; el mejor error medio queda con **Kp = 0.04** (el borde del barrido) y Kd entre 0.0005 y 0.002,
por eso ese es el valor por defecto. Con el robot real habrá que empezar más abajo (ver `docs/armado.md`).

### Sensibilidad: lo que sí hace daño

| Cambio (vbase 0.6) | Error medio QTR-8A | Error medio curvo 24 |
|---|---|---|
| Base (retardo 4 ms) | 1.6 mm | 1.6 mm |
| Retardo 12 ms | **6.8 mm** | **6.8 mm** |
| Retardo 24 ms | **18.4 mm** | **17.5 mm** |
| Ruido ×5 (80 cuentas) | 1.6 mm | 1.6 mm |
| Ruido ×13 (200 cuentas) | 1.9 mm | 2.0 mm |
| Arranca 25 mm desviado | 1.9 mm | 1.9 mm |

Conclusiones honestas:
1. **El retardo entre medir y actuar es el enemigo.** Con 24 canales leídos con emisores encendidos y apagados el ESP32 puede tardar mucho más que con 8.
   Hay que medirlo en el robot (`tel 1` imprime el periodo real en µs). Si pasa de ~4 ms, bajar canales, quitar la lectura con emisores apagados, o usar la variante de 16.
2. **En este modelo el arreglo curvo de 24 no mejora el seguimiento** frente al QTR-8A: la pista de prueba es fácil para ambos. Su ventaja posible
   (más rango lateral, mejor lectura en cruces y esquinas) no está modelada. Decidir por disponibilidad, precio y tiempo de lectura, no por esta simulación.
3. El ruido de lectura casi no importa; la calibración y el retardo sí.

## Gráficas

- `docs/diagramas/sim_base8.png` y `sim_base24.png`: trayectoria sobre la pista y error en el tiempo.
- `docs/diagramas/sim_velocidad.png`: tiempo y error contra velocidad.
- Datos crudos en `sim/resultados/`.

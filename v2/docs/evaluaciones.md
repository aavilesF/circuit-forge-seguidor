# Evaluaciones EN ESTUDIO (no son decisiones) — 13 nov 2026

## 1. Encoders y aprendizaje de pista (P-V2-20)
**Qué da un encoder:** pulsos por vuelta del eje → velocidad real de cada rueda y distancia recorrida. Con eso el robot sabe *dónde* va en la pista (odometría) y puede cerrar el lazo de velocidad (si una rueda patina o la batería baja, lo corrige).

**Sin encoder (lo que tenemos):** el PWM fija voltaje, no velocidad: con la batería bajando de 8.4 a 7 V la velocidad cambia (el MP1584 a 6 V fijos de los motores ya reduce mucho este problema). No hay medida de distancia exacta.

**Aprendizaje sin encoder sí es posible con el ESP32:**
- 1.ª vuelta lenta: con los 12 TCRT5000 el robot calcula la posición de la línea (error del PID) y la registra cada pocos ms junto con el *tiempo*. Curvas = error grande/sostenido; rectas = error ≈ 0. También sirve la diferencia de PWM entre ruedas.
- Se guarda un perfil de pocos KB (p. ej. 1 dato cada 10 ms durante 30 s = 3 000 muestras × 2–4 bytes ≈ 12 KB): cabe de sobra en la RAM (≈ 300 KB) y se puede guardar en la flash con *Preferences*/LittleFS. **No hace falta tarjeta SD.**
- Vueltas siguientes: acelerar en los tramos rectos y frenar *antes* de cada curva. La debilidad: el perfil está indexado por **tiempo**, y si cambia la velocidad se desfasa. Se corrige re-sincronizando con "marcas" que se reconocen con los sensores (inicio de cada curva, discontinuidades de 5 mm).
- Ojo con el reglamento: en eliminatorias son 3 intentos sumados y en finales un solo intento, así que hay que aprender en el primer intento o en práctica antes de la competencia (la pista puede cambiar).

**Comparación**
| Opción | Ventaja | Limitación | Complejidad |
|---|---|---|---|
| 1. Actual (PID + perfil de velocidad por curvatura) | Barato, ya está; PID bien ajustado + velocidad según error ya da mucho | Sin memoria de la pista | Baja |
| 2. Actual + memoria en flash del ESP32 | Frena antes de curvas conocidas; sin hardware nuevo | Desfase por tiempo; se mitiga con marcas | Media |
| 3. N20 con encoder | Velocidad real y distancia; control de velocidad robusto | Comprar 2 motores (~$150–250 c/u), 4 GPIO más, cambiar PCB | Media |
| 4. Encoder + memoria | Lo mejor: mapa por distancia, frenado preciso | Más caro y más firmware | Alta |

**Conclusión:** la ventaja real del encoder es la *precisión* del mapa, no que sin él no se pueda aprender. Con 8 días a la competencia, lo que más tiempo gana es un PID bien ajustado + velocidad variable + memoria simple en el ESP32 (opción 2). **No recomiendo cambiar hardware antes de la PCB.** Si se quisiera dejar la puerta abierta, se podrían reservar 4 GPIO libres (p. ej. GPIO32, 35, 18, 5) en un header en la PCB: requiere tu aprobación.

## 2. Ventilador 4010 (P-V2-21)
- **Mover aire ≠ succionar.** Un ventilador axial 4010 mueve caudal con muy poca presión estática (típ. 2–6 mm H₂O ≈ 20–60 Pa). La fuerza hacia abajo ≈ presión × área sellada: 40 Pa × (0.06 × 0.08 m) ≈ **0.2 N (≈ 20 g)**, y solo si hay una **falda** que casi selle con el piso (holgura < 1–2 mm). Sin falda la ganancia es casi nula.
- **Alimentación:** es de 12 V y lo alimentamos con 7.4–8.4 V → gira a ~60–70 % y la presión cae con el cuadrado de la velocidad (≈ la mitad). Consumo < 1 W (≈ 0.1 A).
- **Costo:** ~15–20 g más soportes y falda, espacio en el chasis, y una falda que roza puede frenar más de lo que ayuda en la pista de fórmica.
- **Recomendación:** no lo quitaría todavía, pero **no lo pondría como prioridad**. Para competir, el agarre se gana más con llantas limpias/blandas y centro de masa bajo. El circuito ya está en la PCB (es barato dejarlo); si en las pruebas no ayuda, simplemente no se monta.
- **Pruebas sencillas:** (1) báscula: poner el robot con ventilador y falda sobre la báscula y comparar el peso aparente encendido/apagado (si baja < 10 g, no sirve); (2) tirar del robot con un dinamómetro o una liga y comparar la fuerza para hacerlo patinar; (3) tiempo de vuelta en la misma curva con y sin ventilador.

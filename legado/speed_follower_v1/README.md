# Speed Follower (rama engineering/speed-follower)

- Entregable 1 (arquitectura): [docs/speed-follower/ARQUITECTURA_SF.md](../docs/speed-follower/ARQUITECTURA_SF.md).
- Entregable 2 (prototipo fabricable, Plan B): [docs/speed-follower/ENTREGABLE_2.md](../docs/speed-follower/ENTREGABLE_2.md) · BOM: [BOM_SF.csv](../docs/speed-follower/BOM_SF.csv).

Simulador Python (numpy, matplotlib):
```bash
cd speed-follower/sim
python3 fase1_calculos.py     # cálculos analíticos: motores, driver, latencia, cuello, barra
python3 barridos_fase1.py     # S1-S6 -> resultados/*.csv (~1 min con 2 núcleos)
python3 robustez.py           # S7: velocidad sostenible por motor y barra (~3 min)
python3 cuello_inercia.py     # S8: cuello con inercia J(L)
python3 graficas.py           # figuras en docs/speed-follower/
```
Archivos: `modelo.py` (motor, robot, pistas), `control.py` (C1 anterior, C2 propuesto), `simular.py` (lazo cerrado).
python3 freno_activo.py       # S9: freno activo (descartado)

Firmware y pruebas (entregable 2):
```bash
speed-follower/pruebas/ejecutar.sh               # control C2 en C++ contra Python (vectores dorados) + propiedades
speed-follower/pruebas/verificar_sintaxis_sf.sh  # firmware ESP32 contra el stub de Arduino (no es compilación real)
cd speed-follower/cad && python3 generar_chasis.py   # chasis paramétrico -> STL, vista PNG, masa
```
Firmware: `firmware/sf/` (abrir `sf.ino`). KiCad (Plan A) pendiente de confirmar tiempos del diseñador de PCB.

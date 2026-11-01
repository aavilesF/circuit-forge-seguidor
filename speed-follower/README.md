# Speed Follower (rama engineering/speed-follower)

Entregable 1 (arquitectura, pendiente de aprobación): [docs/speed-follower/ARQUITECTURA_SF.md](../docs/speed-follower/ARQUITECTURA_SF.md).

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
No hay firmware C++ nuevo, KiCad ni STL en esta etapa (llegan en el entregable 2, tras la aprobación).

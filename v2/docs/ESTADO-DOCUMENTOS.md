# Estado de cada documento (fuente única de "qué es vigente")
Actualizar esta tabla al crear, mover o retirar un documento. `validar_repo.py` comprueba que todos los archivos de `v2/docs/`, `v2/README.md` y `v2/inventario.csv` estén aquí.

| Archivo | Estado | Nota |
|---|---|---|
| `v2/inventario.csv` | **VIGENTE, fuente maestra** del inventario | Se edita a mano; todo lo demás se deriva |
| `v2/docs/componentes.md` | vigente, **generado** | No editar; `generar_componentes.py` |
| `v2/docs/decisiones.md` | vigente | D-V2-xx |
| `docs/pendientes-por-confirmar.md` | vigente (excepción documentada) | Lista única de IDs; historial en `docs/historial/` |
| `v2/docs/pendientes.md` | vigente (puntero) | Solo apunta al anterior |
| `v2/docs/conexiones.md` | vigente | Conexiones, análisis 5 V y estado de las PCB |
| `v2/docs/bibliotecas.md` | vigente | Símbolos y huellas |
| `v2/docs/migracion.md` | vigente, registro | Qué se migró el 12 nov |
| `v2/docs/evaluaciones.md` | vigente, EN ESTUDIO | Encoders y ventilador |
| `v2/docs/optimizacion-pcb-2026-11-14.md` | vigente, registro | Optimización de PCB |
| `v2/docs/ESTADO-DOCUMENTOS.md` | vigente | Este archivo |
| `v2/README.md` | vigente | Índice |
| `docs/requisitos.md` | vigente (excepción) | Reglamento |
| `docs/especificaciones-componentes.md` | vigente (excepción) | Medidas y fuentes; si discrepa del inventario en cantidades, manda `v2/inventario.csv` |
| `docs/historial/` | histórico por diseño | Versiones previas de pendientes |
| `docs/faltantes_robot-casero.md`, `docs/faltantes-unit.md`, `docs/presupuesto.md`, `robot-casero/materiales/BOM.csv` y `CHECKLIST.md` | **HISTÓRICO** | BOM.csv sigue siendo el registro de precios de compra |
| Resto de `docs/*.md`, `docs/robot-casero/`, `electronica/kicad/`, `mecanica/`, `firmware/` (raíz; el vigente es `v2/firmware/emergencia/`), `simulacion/`, `pruebas/`, `modificaciones/` | **HISTÓRICO** | Rama anterior; con aviso al inicio de cada .md |
| `v2/electronica/prototipo-emergencia/` | vigente, ALTERNATIVA de emergencia | Placa perforada, 8 sensores (D-V2-40); esquema único `robot_emergencia_unificado` (D-V2-43, sin JST-RC ni fusible D-V2-45); los esquemas separados `principal_emergencia`/`sensores_emergencia` son la versión anterior; guía de firmware `GUIA-FIRMWARE.md` (EM-05, EM-07); no reemplaza al diseño de PCB |
| `v2/firmware/emergencia/` | **vigente**, firmware del prototipo de emergencia | Adaptado de `firmware/robot-casero/` (EM-07); compilado y probado en PC el 19 nov; falta la prueba física (EM-08) |

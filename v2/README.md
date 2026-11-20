# Seguidor de Línea V2 — rama `seguidor-caseroV2`

Creada el 12 nov 2026 desde `engineering/robot-casero` (commit f9a4700). **Todo lo vigente está en `v2/`.**
El resto de carpetas del repositorio (docs/, electronica/kicad/, mecanica/, firmware/, robot-casero/) se heredó de la rama
anterior y es **HISTÓRICO**: sirve de consulta, no es diseño vigente. No se borró nada.

| Carpeta | Contenido | Estado |
|---|---|---|
| `v2/docs/decisiones.md` | Decisiones vigentes (D-V2-xx) con su origen | vigente |
| `v2/inventario.csv` | **Fuente maestra del inventario** (comprado / usado / recepción) | vigente |
| `v2/docs/componentes.md` | Tabla **generada** desde el inventario; no se edita a mano | vigente |
| `v2/docs/ESTADO-DOCUMENTOS.md` | Qué documentos son vigentes y cuáles históricos | vigente |
| `v2/herramientas/validar_repo.py` | Validador de coherencia (inventario vs esquemas, términos obsoletos, IDs, DRC) | vigente |
| `docs/pendientes-por-confirmar.md` | **Lista única de pendientes** (v10, incluye P-V2-xx) | vigente |
| `v2/docs/conexiones.md` | Qué se conecta con qué y por qué; análisis 3.3 V vs 5 V | vigente |
| `v2/docs/bibliotecas.md` | Qué símbolo usa cada pieza y de dónde viene | vigente |
| `v2/docs/migracion.md` | Qué se migró, qué se corrigió y qué queda histórico | vigente |
| `v2/electronica/principal/` y `sensores/` | Esquemáticos KiCad 10 (copia de los de `SDL V2 General/KiCAD/Esquemas V2`) | esquemas aprobados (D-V2-20) |
| `v2/electronica/principal/` y `sensores/` `.kicad_pcb` | PCB ruteadas, DRC 0 errores (15 nov); sensores = opción B (D-V2-25); la A en `sensores/alternativa_68mm_curva/` | en revisión de Alan |
| `v2/electronica/prototipo-emergencia/` | Prototipo de emergencia en placa perforada: esquema unificado y `GUIA-FIRMWARE.md` | vigente, alternativa (D-V2-40) |
| `v2/firmware/emergencia/` | **Firmware vigente** del prototipo de emergencia (carga, consola, pruebas en PC) | compilado y probado en PC; falta prueba física (EM-08) |
| `v2/electronica/vistas/` | SVG/PNG de esquemas y vistas 3D de la colocación | — |
| `v2/docs/evaluaciones.md` | Encoders/aprendizaje y ventilador (EN ESTUDIO) | — |
| `v2/electronica/herramientas/` | Scripts que generan esquemas, colocación y ruteo | — |

Etapas: 1 esquemáticos (aprobados) → 2 PCB de doble cara (ruteadas, en revisión; sin archivos de fabricación) → 3 compatibilidad mecánica.
Reglas de trabajo: `CLAUDE.md` en la raíz.

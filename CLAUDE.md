# Reglas del proyecto — Seguidor de Línea V2

Rama activa: seguidor-caseroV2.

La versión vigente del proyecto está en v2/.
Los archivos heredados son históricos, salvo las excepciones
expresamente documentadas.

Antes de cerrar cualquier tarea que modifique el repositorio:

1. Ejecutar la skill /mantenimiento-repositorio.
2. Sincronizar inventario, decisiones, pendientes y archivos
   técnicos vigentes que resulten afectados.
3. Comprobar contradicciones entre documentos.
4. Ejecutar las validaciones disponibles.
5. Registrar los cambios confirmados en el mismo commit.

No convertir propuestas en decisiones sin autorización.
No modificar main.
No realizar merges ni force push.

No declarar terminado un trabajo con inconsistencias
sin resolver entre archivos vigentes.

## Validación disponible
- `python3 v2/herramientas/generar_componentes.py` regenera `v2/docs/componentes.md` desde `v2/inventario.csv`.
- `python3 v2/herramientas/validar_repo.py` debe salir sin errores antes de cerrar (inventario vs esquemas, términos obsoletos, IDs, estado de documentos, DRC vs PCB).
- Si cambia un `.kicad_pcb`, repetir DRC y actualizar `v2/electronica/verificacion/registro_drc.json`.

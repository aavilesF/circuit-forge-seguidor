> **HISTÓRICO (rama anterior `engineering/robot-casero`). No es información vigente de V2.** Inventario, decisiones y pendientes vigentes: `v2/inventario.csv`, `v2/docs/decisiones.md`, `docs/pendientes-por-confirmar.md`. Estado de cada documento: `v2/docs/ESTADO-DOCUMENTOS.md`.

# Presupuesto

**Estado:** ningún componente está definido ni comprado. Esta lista parte de la propuesta con ESP32 (ver `plan.md`), todavía sin aprobar.

**Sobre los precios:** la columna de precios son cifras que citó la IA que armó la propuesta. **Nadie las ha verificado** (no traen enlaces) y no incluyen envío. Antes de aprobar el presupuesto, cada precio debe comprobarse en la página de la tienda y anotarse con su enlace.

## Datos confirmados

- Presupuesto estimado por el equipo: entre $600 y $1,000 MXN por persona, o más; todavía sin fijar.
- Se comprará todo nuevo, en línea o en tienda física de León o Irapuato.
- Donación obligatoria para competir: $300 MXN en alimentos por robot (ver `requisitos.md`).
- Peso máximo del robot completo: 500 g.

## Aportaciones

| Integrante | Aportación |
|---|---|
| Alejandro Avilés Flores | Por definir |
| Alan Uzuel Vargas Zavala | Por definir |
| Daniel Navarro Robledo | Por definir |

## Lista propuesta

| Componente | Cant. | Precio citado (MXN, sin verificar) | Subtotal | Estado |
|---|---|---|---|---|
| ESP32 de 38 pines (ESP-WROOM-32) | 1 | 150 | 150 | Por verificar |
| Sensor QTR-8A (o equivalente) | 2 (1 + repuesto) | 280 | 560 | Por verificar |
| Driver TB6612FNG | 2 (1 + repuesto) | 65 | 130 | Por verificar |
| Motores N20 de 6 V (70 a 100 RPM, según la fuente) | 3 (2 + repuesto) | 207.93 | 623.79 | **Revisar: demasiado lentos** (ver `plan.md`) |
| Ruedas para eje D de 3 mm | 2 | 25 | 50 | Por verificar |
| Batería LiPo 2S, 450 a 600 mAh | 1 | 300 (estimado) | 300 | Por cotizar |
| Cargador LiPo balanceador | 1 | 265 | 265 | Por verificar |
| Buck de 5 V (>= 1 A) | 1 | 65 (estimado) | 65 | Por cotizar |
| Buck de 6 V (>= 2 A) | 1 | 85 (estimado) | 85 | Por cotizar |
| Pulsador de arranque | 1 | 30 (estimado) | 30 | Por cotizar |
| Cables y conectores | - | 120 (estimado) | 120 | Por cotizar |
| Multímetro | 1 | 150 | 150 | Por verificar |
| Báscula de 1 g | 1 | 124 | 124 | Por verificar |
| Chasis (impreso o corte láser) | 1 | 300 (estimado) | 300 | Por cotizar |
| Pista de práctica (MDF, papel adhesivo, vinil) | 1 | 750 (estimado) | 750 | Por cotizar |
| Donación de alimentos | 1 | 300 | 300 | Fijo |

Tiendas que mencionó la fuente (sin comprobar): UNIT Electronics, Geek Factory, Kinetrónica, SIEEG, Practinet, Electrónica Cidea, La Resistencia, Aelectronics y Amazon México. Conviene concentrar la compra en una o dos para reducir envíos y retrasos.

## Totales

Suma de la tabla, con las cifras citadas y sin envíos:

| Concepto | Valor |
|---|---|
| Total estimado | $4,002.79 MXN |
| Por persona (tres integrantes) | $1,334.26 MXN |
| Peso total estimado del robot | Entre 150 y 250 g, sin medir (límite: 500 g) |

Corrección respecto a la versión anterior: el bloque de componentes electrónicos se había anotado en unos $2,200, pero los renglones suman $1,513.79, así que el total anterior de $4,689 estaba inflado en unos $686.

El total por persona supera el rango que mencionó el equipo ($600 a $1,000). Una parte (multímetro, báscula, cargador y pista) es inversión única que se queda con el equipo. Recortes posibles: un solo buck de 5 V (ahorra unos $85, motores más lentos) o un solo sensor sin repuesto (ahorra $280, no recomendable).

## Dónde cotizar en persona

- En León: Electrónica Mara, Novedades Electrónicas PH.
- En Irapuato: Electrónica Real, Jimsa Electrónicas.
Datos de un directorio, la disponibilidad hay que confirmarla.

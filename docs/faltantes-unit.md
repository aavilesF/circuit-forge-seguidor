> **HISTÓRICO (rama anterior `engineering/robot-casero`). No es información vigente de V2.** Inventario, decisiones y pendientes vigentes: `v2/inventario.csv`, `v2/docs/decisiones.md`, `docs/pendientes-por-confirmar.md`. Estado de cada documento: `v2/docs/ESTADO-DOCUMENTOS.md`.

# Faltantes y carrito de UNIT (6 nov 2026)

Rama `engineering/robot-casero`. Tienda: <https://uelectronics.com/>. Este documento distingue **en carrito** de **comprado/recibido**: agregar al carrito no significa que el componente ya esté adquirido.

## 1. Carrito informado por Alan (6 nov 2026) — **COMPRADO el 7 nov 2026**

**Actualización 7 nov:** Alan hizo el pedido con estos mismos 9 renglones y cantidades (captura del pedido). Subtotal **$579**, envío **$145** (Estafeta estándar, 1–2 días hábiles), **total $724 MXN**. Las recomendaciones de "no comprar todavía" de la tabla quedan como registro: las ruedas, los 3 IRLZ44N y el kit M3 sí se compraron. Estado de inventario: `robot-casero/materiales/BOM.csv` y `CHECKLIST.md`.

Subtotal declarado por Alan: **$579 MXN**, sin envío. Se verificó la suma de los subtotales de la tabla.

| Producto | Cantidad en carrito | Precio unitario | Subtotal | Evaluación frente al diseño |
|---|---:|---:|---:|---|
| TCRT5000 individual (variante Sensor, no módulo) | 14 | $8 | $112 | Correcto: el diseño usa 12 sensores; 2 quedan de repuesto |
| Módulo CD74HC4067 | 2 | $25 | $50 | El diseño requiere 1; el segundo es repuesto, no imprescindible |
| Mini rueda libre 3Pi N20 | 2 | $16 | $32 | **No comprar todavía**: opción A contempla un patín (O02), no dos ruedas libres. Resolver M30 |
| Soporte N20/N30 blanco ABS | 2 | $5 | $10 | Correcto: 2 soportes para los 2 motores |
| Ventilador 4010 12 V | 1 | $32 | $32 | Variante correcta; ficha: 40×40×10 mm, 100 mA ±10 %, 5000 RPM ±10 %, 5 CFM, 16 g |
| GA12-N20 6 V 1000 RPM | 2 | $89 | $178 | **Coincide con el requisito exacto** del repositorio: 6 V, 1000 RPM, sin encoder |
| Par de cables JST-RC macho/hembra | 2 | $8 | $16 | Útil; comprobar que el conector de descarga de la LiPo sea compatible |
| MOSFET IRLZ44N TO-220 | 3 | $12 | $36 | El diseño requiere 1; 2 adicionales serían repuestos. Confirmar accionamiento con GPIO de 3.3 V |
| Kit de separadores M3 de latón (120 piezas) | 1 | $113 | $113 | **No resuelve directamente** los separadores M3 de 4 mm ni los tornillos M2; mínimo del kit = 6 mm |
| **TOTAL** | | | **$579** | Sin envío |

### 1.1 Recomendaciones antes de pagar

- **Motores:** sí, la variante seleccionada de 6 V y 1000 RPM es la que pide el repositorio. No se ha confirmado todavía el largo/ancho exacto del motor ni la geometría del eje; medir al recibir.
- **Soportes:** cantidad correcta. Ficha: ABS, 25 mm de ancho, 11 mm de alto, abertura/agujero 2 mm, 1.33 g; incluye 2 tornillos M2×7 mm y 2 tuercas M2 por soporte. La ficha no indica el patrón de agujeros para fijarlo a la PCB. No inventar huella.
- **Multiplexor:** el nombre correcto es **74HC4067 / CD74HC4067**, no 74HC6047. Ficha: 2–6 V, 16 canales, 40×20×3 mm, 8 g. El diseño necesita 1; el segundo es opcional.
- **JST-RC:** la ficha indica pitch 2.5 mm, cable 22 AWG, 10 cm. La LiPo debe tener conector de descarga compatible y conector de balance JST-XH de 3 pines para 2S.
- **Ventilador:** la variante de 12 V es la correcta de las disponibles. Pesa 16 g, por lo que debe quedar fijado de forma robusta; según las reglas del proyecto, una pieza de más de 10 g que se desprenda causa falta. La cifra de 5 CFM es nominal a las condiciones del fabricante; no demuestra que el montaje genere succión útil. Requiere cámara/plenum, faldón y prueba en pista. Alimentado desde 2S (7.4–8.4 V) no recibirá sus 12 V nominales y el flujo real será menor.
- **IRLZ44N:** 1 unidad basta según la lista; las otras 2 son repuestos. El datasheet especifica RDS(on) a VGS de 4–5 V, no garantiza el valor a 3.3 V. Como el ESP32 entrega lógica de 3.3 V, Claude debe revisar el circuito de compuerta y considerar un MOSFET con RDS(on) garantizado a 2.5/3.3 V si el IRLZ44N no conmuta plenamente.
- **Ruedas libres:** no son parte de la compra necesaria si se mantiene el patín O02. Quitar las 2 del carrito hasta resolver M30.
- **Kit M3:** no asumir que sustituye los separadores de 4 mm. Sus separadores más cortos son de 6 mm y sus tornillos/tuercas son M3, mientras los soportes de motor incluyen M2. Comprar solo si se acepta rediseñar la altura o si también se necesitan sus otras medidas.

## 2. Componentes que siguen faltando o requieren decisión

| Componente | Cantidad/requisito | Estado | Próxima acción |
|---|---:|---|---|
| PTC rearmable | Selección pendiente | No está en carrito | Revisar en qué rail del esquema está y medir corriente normal; elegir Vmax adecuado |
| Resistencias 1/4 W: 330 Ω | 14 | No están en carrito | Comprar por valor |
| Resistencias 1/4 W: 10 kΩ | 16 | No están en carrito | Comprar por valor |
| Resistencias 1/4 W: 100 Ω | 2 | No están en carrito | Comprar por valor |
| Resistencia 1/4 W: 100 kΩ | 1 | No está en carrito | Comprar |
| Resistencia 1/4 W: 33 kΩ | 1 | No está en carrito | Comprar |
| Header macho 1×15 | 1 | No está en carrito | Confirmar longitud y paso 2.54 mm |
| Header hembra 1×15 | 1 | No está en carrito | Confirmar longitud y paso 2.54 mm |
| Cable plano de 15 hilos o alternativa | 1 tramo | No está en carrito | Revisar cable plano/UTP y longitud |
| Brocas | 1.0 y 1.3 mm | Fuera de UNIT | Ferretería |
| Tornillo M3 de nailon para patín | 1, si se mantiene O02 | Fuera de UNIT | Ferretería |
| Separadores M3 de 4 mm | Según PCB | Pendiente | El kit de 6 mm no es reemplazo directo |
| Tornillos M2 para soportes | Según diseño | Pendiente | Confirmar si los incluidos con los soportes fijan motor o soporte a PCB |
| LiPo 2S | 450–500 mAh, ver sección 3 | Fuera de UNIT | Elegir modelo que quepa y entregue corriente suficiente |

## 3. Requisitos para elegir la batería LiPo

Que aparezca como **7.4 V** es normal: es el voltaje nominal de una batería LiPo 2S. Completamente cargada alcanza **8.4 V**.

Requisito inicial a buscar:
- Química: LiPo.
- Configuración: 2S1P (2 celdas en serie).
- Voltaje: 7.4 V nominal, 8.4 V máximo cargada.
- Capacidad: 450–500 mAh.
- Descarga continua: preferible 20C o más; confirmar contra la corriente real de motores, ventilador y electrónica.
- Descarga pico: especificación del fabricante, no usarla como corriente continua.
- Conector de descarga: compatible con el cable JST-RC elegido; verificar físicamente antes de comprar.
- Balanceo: JST-XH de 3 pines.
- Peso y dimensiones: elegir después de comprobar el espacio real del chasis. No asumir que todas las LiPo 2S de 500 mAh tienen el mismo formato.

Ejemplo de ficha comparable encontrada en web: 500 mAh, 2S, 7.4 V, 20C continua, 30C pico, 55×30×14 mm y 36 g. Es una referencia de especificaciones, **no una recomendación de compra**, porque sus dimensiones y conector podrían no encajar. Ver <https://www.grupoelectrostore.com/producto/bateria-lipo-2s-74v-500mah-turnigy-20c/>.

## 4. Alternativas al PTC radial de 1.5 A

No elegirlo solo por el valor "1.5 A". Primero revisar si protege la entrada de batería 2S o una rama regulada. Si está en la entrada 2S, el voltaje máximo del PTC debe superar 8.4 V con margen. Una alternativa es un PTC radial de 16 V/30 V o superior, o un fusible convencional reemplazable con portafusible; la corriente nominal debe salir del consumo real y de la protección del cableado/PCB. No sustituir hasta revisar el esquema y calcular el valor.

## 5. Presupuesto actualizado

- Ya gastado en Electrónica Valtierra: $510 MXN.
- Carrito UNIT declarado: $579 MXN.
- Pendientes estimados fuera del carrito (LiPo, brocas, patín si se mantiene, tornillería M2/M3 y cable): aprox. $450 MXN, **sin volver a contar los TCRT5000**, que ya están en el carrito.
- Pendientes UNIT que no están en el carrito (PTC, resistencias, headers): aprox. $65 MXN.
- Pista de prueba: aprox. $100 MXN.

**Total preliminar: aprox. $1,704 MXN**, sin envío ni chasis. Es una estimación y deja poco margen contra el máximo de $1,800. Quitar las ruedas libres (-$32) y reducir el IRLZ44N a 1 unidad (-$24) bajaría el total a aprox. $1,648. Si se decide no comprar el kit M3 hasta confirmar su utilidad (-$113), bajaría a aprox. $1,535, antes de comprar los separadores correctos.

## 6. Ventilador y reglas

El ventilador seleccionado pesa 16 g según UNIT. Debe quedar retenido con tornillería/soporte y no depender solo de adhesivo. La succión no puede darse por confirmada por el dato de 5 CFM: hay que diseñar una cámara de presión negativa/faldón y medir si realmente aumenta la carga normal sin rozar la pista. El ventilador solo se activa después de la señal de salida del árbitro, según las reglas del proyecto.

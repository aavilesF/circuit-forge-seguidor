// V2 · Puerto serie virtual por USB (CDC ACM) con el periférico USB FS del STM32G474, registros CMSIS.
// El módulo WeAct trae el USB-C en PA11/PA12; el reloj de 48 MHz es el HSI48 sincronizado con los SOF (CRS).
// Comportamiento según el manual de referencia RM0440 §45 (USB) y la semántica de registros de los controladores de
// ST (stm32g4xx_hal_pcd.h: EPnR con bits de alternancia, PMA de 1 KB con acceso de 16 bits).
// Estado: compila; pendiente de prueba con el módulo real [P].
#pragma once
#include <stdint.h>

namespace usb {

void iniciar();
bool conectado();                              // configurado por el anfitrión y DTR activo (terminal abierta)
uint32_t escribir(const char* s, uint32_t n);  // no bloquea: devuelve los bytes aceptados (el resto se descarta)
void escribir(const char* s);
int leer();                                    // -1 si no hay datos

}  // namespace usb

// Robot casero · capa de hardware del ESP32 (Arduino). Todo lo demás es lógica pura probada en la PC.
#pragma once
#include <stdint.h>

namespace hw {

void iniciar();

// ---- sensores: lecturas crudas 0..4095 de los NUM_SENSORES canales, con LED IR encendidos (on) y apagados (off).
// sobremuestreo: lecturas promediadas por canal. Devuelve los µs que tardó (para la consola `perf`).
uint32_t leer_sensores(int* on, int* off, bool resta_ambiente, uint32_t t_emisor_us, int sobremuestreo);
void emisores(bool encendidos);

// ---- DRV8833: fracción 0..1 del tiempo en alto de cada entrada (motor 0 = izq, 1 = der)
void puente(int motor, float in1, float in2);
void driver_despierto(bool despierto);   // nSLEEP
bool driver_falla();                       // nFAULT en bajo (solo tiene sentido con JP1 cerrado)

// ---- medidas
float v_divisor();                         // V en la entrada del divisor (VBAT después de D1), promediada

// ---- interfaz
bool boton_start();                        // true = oprimido (sin rebote: lo filtra quien llama)
bool boton_cal();
void led(bool encendido);
void zumbador(uint16_t hz, bool activo);   // hz = 0 calla

}  // namespace hw

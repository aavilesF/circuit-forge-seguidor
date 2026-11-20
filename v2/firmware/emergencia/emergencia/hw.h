// Robot de emergencia · capa de hardware del ESP32 (Arduino). Todo lo demás es lógica pura probada en la PC.
#pragma once
#include <stdint.h>

namespace hw {

void iniciar();   // primero deja el DRV8833 dormido y las entradas del puente en 0

// ---- sensores: lecturas crudas 0..4095 en ORDEN FÍSICO (índice 0 = izquierda), con LED IR encendidos (on) y
// apagados (off). sobremuestreo: lecturas promediadas por canal. Devuelve los µs que tardó (consola `perf`).
uint32_t leer_sensores(int* on, int* off, bool resta_ambiente, uint32_t t_emisor_us, int sobremuestreo);
int leer_canal(int canal, int sobremuestreo);   // un canal del mux (0..15), sin tocar los emisores
void emisores(bool encendidos);
bool emisores_encendidos();

// ---- DRV8833: fracción 0..1 del tiempo en alto de cada entrada (motor 0 = izq, 1 = der)
void puente(int motor, float in1, float in2);
void driver_despierto(bool despierto);   // nSLEEP
bool driver_esta_despierto();

// ---- medidas
float v_bateria();                         // V de la batería (divisor directo a VBAT_SW), promediada
float mv_pin_bateria();                    // mV en GPIO36

// ---- interfaz
bool boton_start();                        // true = oprimido (sin rebote: lo filtra quien llama)
bool boton_cal();
void led(bool encendido);

}  // namespace hw

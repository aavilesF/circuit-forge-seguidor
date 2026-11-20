// Robot de emergencia · capa de hardware del ESP32 (Arduino-ESP32 2.0.17 y 3.x). Todo lo demás es lógica pura
// probada en la PC. Sin WiFi ni Bluetooth: no se incluye ninguna de sus bibliotecas (reglamento).
#pragma once
#include <stdint.h>

namespace hw {

void iniciar();   // primero deja el DRV8833 dormido y las 4 entradas del puente en 0

// ---- sensores
struct ConfigLectura {
  bool resta_ambiente = true;
  bool invertidos = false;     // true: el sensor lógico 0 (izquierda) es SEN8 (C7)
  uint32_t t_emisor_us = 150;  // espera tras prender/apagar los LED IR
  uint32_t t_mux_us = 5;       // espera tras cambiar el canal
  int sobremuestreo = 2;       // lecturas promediadas por canal (1..4)
  int descartes = 1;           // lecturas tiradas tras cambiar de canal (0..3)
};
// Lecturas crudas 0..4095 en ORDEN FÍSICO (índice 0 = izquierda): primero con LED IR apagados (off = luz ambiente),
// luego encendidos (on). Deja los LED apagados. Devuelve los µs que tardó (consola `perf`).
uint32_t leer_sensores(int* on, int* off, const ConfigLectura& c);
int leer_canal(int canal, const ConfigLectura& c);   // un canal del mux (0..15), sin tocar los emisores
void seleccionar_canal(int canal, uint32_t t_mux_us);
void emisores(bool encendidos);
bool emisores_encendidos();

// ---- DRV8833: fracción 0..1 del tiempo en alto de cada entrada (motor 0 = AIN = M1, 1 = BIN = M2)
void puente(int motor, float in1, float in2);
void driver_despierto(bool despierto);   // nSLEEP
bool driver_esta_despierto();

// ---- medidas
float v_bateria();                         // V de la batería (divisor directo a VBAT_SW), promedio de 4
float mv_pin_bateria();                    // mV en GPIO36 (calibración de fábrica del ADC)
int adc_crudo_bateria();                   // cuentas crudas 0..4095 en GPIO36, promedio de 8 (diagnóstico)

// ---- interfaz
bool boton_start();                        // true = oprimido (sin rebote: lo filtra quien llama)
bool boton_cal();
void led(bool encendido);

// ---- watchdog de hardware (Task WDT): reinicia el ESP32 si loop() deja de alimentarlo `ms` milisegundos.
// Tras el reinicio el DRV8833 queda dormido (pull-down interno de nSLEEP) y setup() lo deja así.
bool vigilante_iniciar(uint32_t ms);
void vigilante_alimentar();

// ---- información
uint32_t cpu_mhz();
const char* version_nucleo();

}  // namespace hw

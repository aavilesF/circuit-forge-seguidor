// Capa de hardware del STM32G431CBT6 en la PCB-chasis (registros CMSIS, sin HAL).
// Los pines salen de pines_generados.h (generado del mismo diseño que el esquemático y la PCB).
#pragma once
#include <stdint.h>

namespace hw {

constexpr uint32_t F_CPU = 170000000u;      // HSI16 -> PLL (M 4, N 85, R 2)

void iniciar();                              // reloj, GPIO, ADC, PWM, encoders, UART, base de tiempo

// ---- tiempo
uint32_t ms();                               // milisegundos desde el arranque (SysTick)
uint32_t ciclos();                           // contador de ciclos (DWT), 170 por µs
void espera_us(uint32_t us);
bool tick_control();                         // true una vez por periodo de control (TIM6, 1 kHz)

// ---- sensores: lectura con emisores apagados (luz ambiente) y encendidos
// raw_* en cuentas de 12 bits, índice = sensor (0 = S1, izquierda). v_bat en voltios (ADC2, lectura "apagado").
void leer_sensores(uint16_t* raw_apagado, uint16_t* raw_encendido, float* v_bat, bool resta_ambiente, uint32_t t_emisor_us);
void emisores(bool encendidos);

// ---- motores (DRV8833, decaimiento lento): ciclo con signo -1..1 relativo a Vbat; habilita nSLEEP
void motores(float izq, float der);
void motores_apagar();                       // nSLEEP en bajo (salidas en alta impedancia)
bool falla_driver();                         // nFAULT en bajo

// ---- encoders (TIM2 izquierdo, TIM3 derecho), cuentas acumuladas con signo (4 flancos)
int32_t encoder_izq();
int32_t encoder_der();

// ---- interfaz
bool boton_start();                          // true = presionado
bool boton_cal();
void led_ok(bool on);
void led_error(bool on);

// ---- puerto serie (USART1 -> conector STDC14 -> STLINK-V3MINIE)
void serie_escribir(const char* s);
void serie_escribir(const char* s, uint32_t n);
int serie_leer();                            // -1 si no hay datos

// ---- memoria no volátil (última página de 2 KB de la flash)
bool flash_guardar(const void* datos, uint32_t n);   // n múltiplo de 8, ≤ 2048
const void* flash_datos();

}  // namespace hw

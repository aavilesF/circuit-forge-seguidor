// V2 · Capa de hardware del STM32G474CEU6 (módulo WeAct en la PCB principal V2). Registros CMSIS, sin HAL.
// Pines: pines_v2.h (generado de hardware/v2/electronica/generador/principal.py; funciones alternas verificadas con
// STM32_open_pin_data de ST). Referencias: RM0440 (manual de referencia STM32G4), DS12288 (STM32G474xB/xC/xE),
// DRV8874 SLVSF66A, ISM330DHCX y LPS22DF (registros de los controladores oficiales de ST, ism330dhcx-pid, lps22df-pid).
#pragma once
#include <stdint.h>

namespace hw2 {

constexpr uint32_t F_CPU = 170000000u;       // HSE 8 MHz del módulo -> PLL (M 2, N 85, R 2); HSI16 si el cristal falla

void iniciar();
bool reloj_con_cristal();                    // false si arrancó con el HSI16 (el USB sigue con HSI48 + CRS)

// ---- tiempo
uint32_t ms();
uint32_t ciclos();                           // DWT, 170 por µs
void espera_us(uint32_t us);
bool tick_control();                         // una vez por ms (TIM6)

// ---- barra de sensores (2 × 74HC4051 + emisores con AO3400A): 16 lecturas con emisores apagados y encendidos.
// mux[i], canal[i] = multiplexor y canal del sensor i (config_v2.h). Lee los dos multiplexores a la vez (ADC1 y ADC2).
void leer_barra(uint16_t* ambiente, uint16_t* encendido, uint32_t t_emisor_us);
// ---- analógicas
float v_bateria();                           // V (divisor R3/R4)
void corrientes(float* i_izq, float* i_der); // A, IPROPI de cada DRV8874 (|I| del transistor bajo)

// ---- puentes H DRV8874 en modo PH/EN (PMODE a GND): PH = sentido, EN = PWM de 20 kHz (TIM1 CH3 izq., CH2 der.)
// ciclo con signo −1..1; despierto = nSLEEP en alto; frenar = EN en 0 con el puente despierto (freno de bajo lado).
void motores(float izq, float der, bool despierto, bool frenar);
bool nfault();                               // nFAULT en bajo

// ---- encoders (TIM4 izquierdo de 16 bits extendido a 32, TIM2 derecho de 32 bits), 4 flancos
int32_t encoder_izq();
int32_t encoder_der();

// ---- I2C3 (PA8 SCL, PC11 SDA, ≈ 400 kHz): IMU y barómetros. Devuelven false si el dispositivo no responde.
bool i2c_escribir(uint8_t dir7, uint8_t reg, uint8_t valor);
bool i2c_leer(uint8_t dir7, uint8_t reg, uint8_t* datos, uint32_t n);

// ---- ESC del ventilador: DShot300 por PB9 (TIM17 CH1 + DMA). valor 0 = parado/desarmado, 48..2047 = acelerador.
void esc_dshot(uint16_t valor);
uint16_t dshot_trama(uint16_t valor, bool telemetria);   // trama de 16 bits con CRC (pública para las pruebas)

// ---- interfaz
void zumbador(uint16_t hz);                  // 0 = silencio (TIM16 CH1 en PB8)
void leds(bool verde, bool amarillo, bool rojo, bool succion);
bool boton_start();                          // true = presionado
bool boton_cal();

// ---- memoria no volátil: últimos 2 KB de la flash (0x0807F800)
bool flash_guardar(const void* datos, uint32_t n);       // n múltiplo de 8, ≤ 2048
const void* flash_datos();

}  // namespace hw2

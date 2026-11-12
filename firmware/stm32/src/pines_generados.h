// GENERADO por herramientas/generar_config_firmware.py desde hardware/electronics/generador/diseno.py.
// NO EDITAR A MANO: los pines salen del mismo diseño que el esquemático y la PCB.
#pragma once
#include <stdint.h>

namespace pin {
struct Gpio { char puerto; uint8_t num; int8_t af; };   // af = -1: GPIO o analógico
constexpr Gpio BTN_CAL = {'C', 14, -1};   // PC14 GPIO_IN
constexpr Gpio BTN_START = {'C', 13, -1};   // PC13 GPIO_IN
constexpr Gpio DRV_FAULT = {'C', 15, -1};   // PC15 GPIO_IN
constexpr Gpio DRV_SLEEP = {'B', 10, -1};   // PB10 GPIO_OUT
constexpr Gpio EMIT_G = {'B', 9, -1};   // PB9 GPIO_OUT
constexpr Gpio ENC_L_A = {'A', 15, 1};   // PA15 TIM2_CH1
constexpr Gpio ENC_L_B = {'B', 3, 1};   // PB3 TIM2_CH2
constexpr Gpio ENC_R_A = {'B', 4, 2};   // PB4 TIM3_CH1
constexpr Gpio ENC_R_B = {'B', 5, 2};   // PB5 TIM3_CH2
constexpr Gpio LED_ERR = {'A', 12, -1};   // PA12 GPIO_OUT
constexpr Gpio LED_OK = {'B', 13, -1};   // PB13 GPIO_OUT
constexpr Gpio PWM_AIN1 = {'A', 8, 6};   // PA8 TIM1_CH1
constexpr Gpio PWM_AIN2 = {'A', 9, 6};   // PA9 TIM1_CH2
constexpr Gpio PWM_BIN1 = {'A', 11, 11};   // PA11 TIM1_CH4
constexpr Gpio PWM_BIN2 = {'A', 10, 6};   // PA10 TIM1_CH3
constexpr Gpio SWCLK = {'A', 14, 0};   // PA14 SYS_JTCK-SWCLK
constexpr Gpio SWDIO = {'A', 13, 0};   // PA13 SYS_JTMS-SWDIO
constexpr Gpio UART_RX = {'B', 7, 7};   // PB7 USART1_RX
constexpr Gpio UART_TX = {'B', 6, 7};   // PB6 USART1_TX
// Canal de TIM1 que maneja cada entrada del DRV8833
constexpr int CANAL_AIN1 = 1;
constexpr int CANAL_AIN2 = 2;
constexpr int CANAL_BIN1 = 4;
constexpr int CANAL_BIN2 = 3;
// ADC1: secuencia regular (sensor -1 = batería)
constexpr int ADC1_N = 8;
constexpr uint8_t ADC1_CANAL[ADC1_N] = {5, 11, 12, 15, 4, 3, 2, 10};
constexpr int8_t ADC1_SENSOR[ADC1_N] = {0, 1, 4, 5, 10, 11, 12, 15};
constexpr Gpio ADC1_PIN[ADC1_N] = {{'B', 14, -1}, {'B', 12, -1}, {'B', 1, -1}, {'B', 0, -1}, {'A', 3, -1}, {'A', 2, -1}, {'A', 1, -1}, {'F', 0, -1}};
// ADC2: secuencia regular (sensor -1 = batería)
constexpr int ADC2_N = 9;
constexpr uint8_t ADC2_CANAL[ADC2_N] = {14, 12, 4, 3, 13, 17, 1, 10, 15};
constexpr int8_t ADC2_SENSOR[ADC2_N] = {2, 3, 6, 7, 8, 9, 13, 14, -1};
constexpr Gpio ADC2_PIN[ADC2_N] = {{'B', 11, -1}, {'B', 2, -1}, {'A', 7, -1}, {'A', 6, -1}, {'A', 5, -1}, {'A', 4, -1}, {'A', 0, -1}, {'F', 1, -1}, {'B', 15, -1}};
constexpr float DIVISOR_VBAT = 4.030303f;   // (R3 + R4) / R4
}  // namespace pin

// GENERADO por firmware/v2/herramientas/generar_config.py desde hardware/v2/electronica/generador/principal.py.
// Funciones alternas y canales de ADC: STM32_open_pin_data (ST), STM32G474C(B-C-E)Ux [V].
#pragma once
#include <stdint.h>

namespace pin2 {

struct Gpio { char puerto; uint8_t num; uint8_t af; };
struct Analogica { char puerto; uint8_t num; uint8_t adc; uint8_t canal; };

constexpr Gpio BTN_CAL{'A', 5, 0};   // PA5
constexpr Gpio BTN_START{'C', 4, 0};   // PC4
constexpr Gpio DRV_nFAULT{'B', 12, 0};   // PB12
constexpr Gpio DRV_nSLEEP{'B', 4, 0};   // PB4
constexpr Gpio EMIT{'A', 4, 0};   // PA4
constexpr Gpio ENC_D_A{'A', 15, 1};   // PA15 AF1
constexpr Gpio ENC_D_B{'B', 3, 1};   // PB3 AF1
constexpr Gpio ENC_I_A{'B', 6, 2};   // PB6 AF2
constexpr Gpio ENC_I_B{'B', 7, 2};   // PB7 AF2
constexpr Gpio EN_D{'A', 9, 6};   // PA9 AF6
constexpr Gpio EN_I{'A', 10, 6};   // PA10 AF6
constexpr Gpio ESC_SEN{'B', 9, 1};   // PB9 AF1
constexpr Gpio I2C_SCL{'A', 8, 2};   // PA8 AF2
constexpr Gpio I2C_SDA{'C', 11, 8};   // PC11 AF8
constexpr Analogica IPROPI_D{'B', 2, 2, 12};   // PB2 ADC2_IN12
constexpr Analogica IPROPI_I{'A', 3, 1, 4};   // PA3 ADC1_IN4
constexpr Gpio LED_AMARILLO{'B', 1, 0};   // PB1
constexpr Gpio LED_ROJO{'B', 10, 0};   // PB10
constexpr Gpio LED_VERDE{'B', 0, 0};   // PB0
constexpr Gpio MUX_S0{'B', 13, 0};   // PB13
constexpr Gpio MUX_S1{'B', 14, 0};   // PB14
constexpr Gpio MUX_S2{'B', 15, 0};   // PB15
constexpr Gpio PH_D{'B', 5, 0};   // PB5
constexpr Gpio PH_I{'C', 10, 0};   // PC10
constexpr Analogica SENS_A{'A', 0, 1, 1};   // PA0 ADC1_IN1
constexpr Analogica SENS_B{'A', 1, 2, 2};   // PA1 ADC2_IN2
constexpr Analogica VBAT_MED{'A', 2, 1, 3};   // PA2 ADC1_IN3
constexpr Gpio ZUMB{'B', 8, 1};   // PB8 AF1
constexpr Gpio LED_SUCCION{'C', 6, 0};   // PC6: LED azul del módulo WeAct [V esquemático WeAct]

}  // namespace pin2

// V2 · Capa de hardware del STM32G474CEU6 (registros CMSIS). Ver hw_v2.h.
#include "hw_v2.h"

#include "../../config_v2.h"
#include "pines_v2.h"
#include "stm32g4xx.h"

extern "C" uint32_t SystemCoreClock;

namespace hw2 {
namespace {

volatile uint32_t g_ms = 0;
volatile bool g_tick = false;
bool g_cristal = false;
constexpr uint32_t PWM_ARR = F_CPU / 20000u - 1u;             // 8499: 20 kHz (config_v2.h F_PWM)
constexpr uint32_t FLASH_DIR = 0x0807F800u;                    // últimos 2 KB (el enlazador reserva los últimos 4 KB)
constexpr bool LED_SUCCION_ALTO = true;                        // nivel activo del LED azul del módulo [P: verificar]
constexpr uint32_t I2C_TIMINGR = 0x1032040Au;                  // ver i2c_iniciar()
// DShot300: bit de 567 ciclos de 170 MHz = 3.335 µs (299.8 kbit/s); 1 = 75 %, 0 = 37.5 % del bit (protocolo DShot)
constexpr uint32_t DSHOT_ARR = 566u, DSHOT_T1 = 425u, DSHOT_T0 = 213u;
constexpr uint32_t DMAMUX_TIM17_UP = 85u;                      // RM0440 tabla DMAMUX [V: stm32g4xx_hal_dma.h]
volatile uint32_t g_dshot[18];

GPIO_TypeDef* puerto(char p) {
  switch (p) {
    case 'A': return GPIOA;
    case 'B': return GPIOB;
    case 'C': return GPIOC;
    default: return GPIOF;
  }
}

enum Modo : uint32_t { ENTRADA = 0, SALIDA = 1, ALTERNA = 2, ANALOGICA = 3 };

void configurar(char pt, uint8_t n, Modo m, uint8_t af = 0, uint32_t pupd = 0, uint32_t velocidad = 1, bool od = false) {
  GPIO_TypeDef* P = puerto(pt);
  P->MODER = (P->MODER & ~(3u << (2 * n))) | (uint32_t(m) << (2 * n));
  P->PUPDR = (P->PUPDR & ~(3u << (2 * n))) | (pupd << (2 * n));
  P->OSPEEDR = (P->OSPEEDR & ~(3u << (2 * n))) | (velocidad << (2 * n));
  if (od) P->OTYPER |= (1u << n); else P->OTYPER &= ~(1u << n);
  if (m == ALTERNA) {
    volatile uint32_t& afr = P->AFR[n >> 3];
    const uint32_t s = 4 * (n & 7);
    afr = (afr & ~(0xFu << s)) | (uint32_t(af) << s);
  }
}
void configurar(const pin2::Gpio& g, Modo m, uint32_t pupd = 0, uint32_t vel = 1, bool od = false) {
  configurar(g.puerto, g.num, m, g.af, pupd, vel, od);
}
inline void escribir(const pin2::Gpio& g, bool v) { puerto(g.puerto)->BSRR = v ? (1u << g.num) : (1u << (g.num + 16)); }
inline bool leer(const pin2::Gpio& g) { return (puerto(g.puerto)->IDR >> g.num) & 1u; }

// ------------------------------------------------------------------ reloj
// HSE 8 MHz (cristal del módulo WeAct) -> PLL: 8/2·85/2 = 170 MHz, rango 1 en modo boost, 4 estados de espera
// (RM0440 §5.1.5 y §3.3.3). Si el cristal no arranca, HSI16/4·85/2 = 170 MHz (como V1). USB: HSI48 con CRS
// sincronizado a los SOF del USB (AN2606: así arranca también el cargador DFU del G474).
void reloj() {
  RCC->APB1ENR1 |= RCC_APB1ENR1_PWREN;
  (void)RCC->APB1ENR1;
  PWR->CR5 &= ~PWR_CR5_R1MODE;
  FLASH->ACR = (FLASH->ACR & ~FLASH_ACR_LATENCY) | FLASH_ACR_LATENCY_4WS | FLASH_ACR_PRFTEN | FLASH_ACR_ICEN | FLASH_ACR_DCEN;
  while ((FLASH->ACR & FLASH_ACR_LATENCY) != FLASH_ACR_LATENCY_4WS) {}
  RCC->CR |= RCC_CR_HSION;                                       // HSI16: reloj del I2C3 aunque el sistema use el HSE
  while (!(RCC->CR & RCC_CR_HSIRDY)) {}
  RCC->CR |= RCC_CR_HSEON;
  for (uint32_t n = 0; n < 400000u && !(RCC->CR & RCC_CR_HSERDY); ++n) {}
  g_cristal = (RCC->CR & RCC_CR_HSERDY) != 0;
  if (g_cristal)
    RCC->PLLCFGR = RCC_PLLCFGR_PLLSRC_HSE | ((2 - 1) << RCC_PLLCFGR_PLLM_Pos) | (85 << RCC_PLLCFGR_PLLN_Pos) |
                   (0 << RCC_PLLCFGR_PLLR_Pos) | RCC_PLLCFGR_PLLREN;
  else
    RCC->PLLCFGR = RCC_PLLCFGR_PLLSRC_HSI | ((4 - 1) << RCC_PLLCFGR_PLLM_Pos) | (85 << RCC_PLLCFGR_PLLN_Pos) |
                   (0 << RCC_PLLCFGR_PLLR_Pos) | RCC_PLLCFGR_PLLREN;
  RCC->CR |= RCC_CR_PLLON;
  while (!(RCC->CR & RCC_CR_PLLRDY)) {}
  RCC->CFGR = (RCC->CFGR & ~RCC_CFGR_HPRE) | RCC_CFGR_HPRE_DIV2;  // paso intermedio > 80 MHz (RM0440 §7.2.7)
  RCC->CFGR = (RCC->CFGR & ~RCC_CFGR_SW) | RCC_CFGR_SW_PLL;
  while ((RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_PLL) {}
  for (volatile int i = 0; i < 200; ++i) {}
  RCC->CFGR &= ~RCC_CFGR_HPRE;
  SystemCoreClock = F_CPU;
  // 48 MHz del USB
  RCC->CRRCR |= RCC_CRRCR_HSI48ON;
  while (!(RCC->CRRCR & RCC_CRRCR_HSI48RDY)) {}
  RCC->CCIPR &= ~RCC_CCIPR_CLK48SEL;                             // 00 = HSI48
  RCC->APB1ENR1 |= RCC_APB1ENR1_CRSEN;
  (void)RCC->APB1ENR1;
  CRS->CFGR = (CRS->CFGR & ~CRS_CFGR_SYNCSRC) | CRS_CFGR_SYNCSRC_1;   // 10 = SOF del USB
  CRS->CR |= CRS_CR_AUTOTRIMEN | CRS_CR_CEN;
}

// ------------------------------------------------------------------ ADC1 y ADC2 (reloj síncrono HCLK/4 = 42.5 MHz)
void adc_iniciar(ADC_TypeDef* A) {
  A->CR &= ~ADC_CR_DEEPPWD;
  A->CR |= ADC_CR_ADVREGEN;
  espera_us(30);
  A->CR &= ~ADC_CR_ADCALDIF;
  A->CR |= ADC_CR_ADCAL;
  while (A->CR & ADC_CR_ADCAL) {}
  espera_us(2);
  A->ISR = ADC_ISR_ADRDY;
  A->CR |= ADC_CR_ADEN;
  while (!(A->ISR & ADC_ISR_ADRDY)) {}
  A->CFGR = ADC_CFGR_OVRMOD;                                     // 12 bits, a la derecha, disparo por software
  // muestreo de 47.5 ciclos (1.1 µs; sensores de 10 kΩ y IPROPI de 1.5 kΩ); batería (24.8 kΩ): 92.5 ciclos
  uint32_t s1 = 0, s2 = 0;
  for (int c = 0; c < 10; ++c) s1 |= 4u << (3 * c);
  for (int c = 0; c < 9; ++c) s2 |= 4u << (3 * c);
  s1 = (s1 & ~(7u << (3 * pin2::VBAT_MED.canal))) | (5u << (3 * pin2::VBAT_MED.canal));
  A->SMPR1 = s1;
  A->SMPR2 = s2;
}

inline void adc_arrancar(ADC_TypeDef* A, uint32_t canal) {
  A->SQR1 = canal << ADC_SQR1_SQ1_Pos;
  A->CR |= ADC_CR_ADSTART;
}

inline uint16_t adc_esperar(ADC_TypeDef* A) {
  uint32_t n = 0;
  while (!(A->ISR & ADC_ISR_EOC)) { if (++n > 20000u) return 0; }
  return uint16_t(A->DR);
}

void mux(uint8_t c) {
  escribir(pin2::MUX_S0, c & 1u);
  escribir(pin2::MUX_S1, c & 2u);
  escribir(pin2::MUX_S2, c & 4u);
}

// Los dos multiplexores a la vez: canal c de U17 en ADC1 (SENS_A) y de U18 en ADC2 (SENS_B).
void barrido(uint16_t* sensor) {
  uint16_t lect[2][8];
  for (uint8_t c = 0; c < 8; ++c) {
    mux(c);
    espera_us(3);                                                // conmutación del 74HC4051 y carga de la entrada [S]
    adc_arrancar(ADC1, pin2::SENS_A.canal);
    adc_arrancar(ADC2, pin2::SENS_B.canal);
    lect[0][c] = adc_esperar(ADC1);
    lect[1][c] = adc_esperar(ADC2);
  }
  for (int i = 0; i < cfg2::N_SENSORES; ++i) sensor[i] = lect[cfg2::SENSOR_MUX[i]][cfg2::SENSOR_CANAL[i]];
}

// ------------------------------------------------------------------ I2C3
void i2c_recuperar_bus() {
  // si un esclavo quedó a mitad de un byte (reinicio durante una lectura), SDA queda en bajo: 9 pulsos de SCL lo liberan
  configurar(pin2::I2C_SCL, SALIDA, 0, 1, true);
  configurar(pin2::I2C_SDA, ENTRADA);
  for (int k = 0; k < 9 && !leer(pin2::I2C_SDA); ++k) {
    escribir(pin2::I2C_SCL, false); espera_us(5);
    escribir(pin2::I2C_SCL, true); espera_us(5);
  }
}

void i2c_iniciar() {
  RCC->CCIPR = (RCC->CCIPR & ~RCC_CCIPR_I2C3SEL) | (2u << RCC_CCIPR_I2C3SEL_Pos);   // 10 = HSI16
  RCC->APB1ENR1 |= RCC_APB1ENR1_I2C3EN;
  (void)RCC->APB1ENR1;
  escribir(pin2::I2C_SCL, true);
  i2c_recuperar_bus();
  configurar(pin2::I2C_SCL, ALTERNA, 0, 1, true);                // drenaje abierto; pull-ups de 2.2 kΩ en la placa (R9/R10)
  configurar(pin2::I2C_SDA, ALTERNA, 0, 1, true);
  I2C3->CR1 = 0;
  // TIMINGR con I2CCLK = 16 MHz [C, fórmula de RM0440 §39.4.10]: PRESC 1 (125 ns), SCLL 10 -> tLOW = 1.375 µs ≥ 1.3,
  // SCLH 4 -> tHIGH = 0.625 µs ≥ 0.6, SDADEL 2 (250 ns), SCLDEL 3 (500 ns ≥ 100). Más la sincronización: ≈ 380-400 kHz.
  I2C3->TIMINGR = I2C_TIMINGR;
  I2C3->CR1 = I2C_CR1_PE;
}

bool i2c_esperar(uint32_t bandera) {
  const uint32_t t0 = DWT->CYCCNT;
  while (!(I2C3->ISR & bandera)) {
    if (I2C3->ISR & (I2C_ISR_NACKF | I2C_ISR_BERR | I2C_ISR_ARLO) || DWT->CYCCNT - t0 > F_CPU / 2000u) {   // 0.5 ms
      I2C3->ICR = I2C_ICR_NACKCF | I2C_ICR_BERRCF | I2C_ICR_ARLOCF;
      if (!(I2C3->ISR & I2C_ISR_STOPF)) I2C3->CR2 |= I2C_CR2_STOP;
      const uint32_t t1 = DWT->CYCCNT;
      while (!(I2C3->ISR & I2C_ISR_STOPF) && DWT->CYCCNT - t1 < F_CPU / 10000u) {}
      I2C3->ICR = I2C_ICR_STOPCF;
      return false;
    }
  }
  return true;
}

// ------------------------------------------------------------------ puentes H
inline void puente(volatile uint32_t& ccr, const pin2::Gpio& ph, float d) {
  if (d > 1.0f) d = 1.0f;
  if (d < -1.0f) d = -1.0f;
  escribir(ph, d >= 0.0f);                                       // PH = 1: OUT1 -> OUT2 (adelante) [V tabla PH/EN]
  ccr = uint32_t((d >= 0.0f ? d : -d) * float(PWM_ARR + 1));     // EN = PWM; EN = 0 frena (bajo lado)
}

}  // namespace

// ================================================================== público
bool reloj_con_cristal() { return g_cristal; }

void iniciar() {
  DCB->DEMCR |= DCB_DEMCR_TRCENA_Msk;                            // contador de ciclos (lo usa espera_us en reloj())
  DWT->CYCCNT = 0;
  DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
  reloj();
  RCC->AHB1ENR |= RCC_AHB1ENR_DMA1EN | RCC_AHB1ENR_DMAMUX1EN;
  RCC->AHB2ENR |= RCC_AHB2ENR_GPIOAEN | RCC_AHB2ENR_GPIOBEN | RCC_AHB2ENR_GPIOCEN | RCC_AHB2ENR_GPIOFEN | RCC_AHB2ENR_ADC12EN;
  RCC->APB1ENR1 |= RCC_APB1ENR1_TIM2EN | RCC_APB1ENR1_TIM4EN | RCC_APB1ENR1_TIM6EN;
  RCC->APB2ENR |= RCC_APB2ENR_TIM1EN | RCC_APB2ENR_TIM16EN | RCC_APB2ENR_TIM17EN | RCC_APB2ENR_SYSCFGEN;
  (void)RCC->APB2ENR;
  SysTick_Config(F_CPU / 1000);

  // salidas seguras primero: puentes dormidos, emisores apagados, EN en 0
  escribir(pin2::DRV_nSLEEP, false); configurar(pin2::DRV_nSLEEP, SALIDA);
  escribir(pin2::EMIT, false); configurar(pin2::EMIT, SALIDA);
  escribir(pin2::PH_I, false); configurar(pin2::PH_I, SALIDA);
  escribir(pin2::PH_D, false); configurar(pin2::PH_D, SALIDA);
  for (const pin2::Gpio& g : {pin2::LED_VERDE, pin2::LED_AMARILLO, pin2::LED_ROJO, pin2::MUX_S0, pin2::MUX_S1, pin2::MUX_S2}) {
    escribir(g, false); configurar(g, SALIDA);
  }
  escribir(pin2::LED_SUCCION, !LED_SUCCION_ALTO); configurar(pin2::LED_SUCCION, SALIDA);
  configurar(pin2::BTN_START, ENTRADA);                          // pull-up externo (R11/R12) y RC de antirrebote
  configurar(pin2::BTN_CAL, ENTRADA);
  configurar(pin2::DRV_nFAULT, ENTRADA);                         // pull-up externo R23

  // EN de los puentes: TIM1 CH3 (PA10, izquierdo) y CH2 (PA9, derecho), PWM 1 a 20 kHz, arranca en 0 (freno)
  configurar(pin2::EN_I, ALTERNA, 0, 2);
  configurar(pin2::EN_D, ALTERNA, 0, 2);
  TIM1->PSC = 0;
  TIM1->ARR = PWM_ARR;
  const uint32_t pwm1 = TIM_CCMR1_OC1M_1 | TIM_CCMR1_OC1M_2;
  TIM1->CCMR1 = (pwm1 << 8) | TIM_CCMR1_OC2PE;
  TIM1->CCMR2 = pwm1 | TIM_CCMR2_OC3PE;
  TIM1->CCR2 = TIM1->CCR3 = 0;
  TIM1->CCER = TIM_CCER_CC2E | TIM_CCER_CC3E;
  TIM1->BDTR = TIM_BDTR_MOE;
  TIM1->CR1 = TIM_CR1_ARPE;
  TIM1->EGR = TIM_EGR_UG;
  TIM1->CR1 |= TIM_CR1_CEN;

  // encoders: TIM4 (izquierdo, PB6/PB7) y TIM2 (derecho, PA15/PB3), modo 3 (4 flancos), filtro fDTS/16 N = 8
  configurar(pin2::ENC_I_A, ALTERNA); configurar(pin2::ENC_I_B, ALTERNA);
  configurar(pin2::ENC_D_A, ALTERNA); configurar(pin2::ENC_D_B, ALTERNA);
  TIM_TypeDef* const enc[2] = {TIM4, TIM2};
  for (TIM_TypeDef* T : enc) {
    T->CCMR1 = TIM_CCMR1_CC1S_0 | TIM_CCMR1_CC2S_0 | (0xAu << TIM_CCMR1_IC1F_Pos) | (0xAu << TIM_CCMR1_IC2F_Pos);
    T->CCER = 0;
    T->SMCR = TIM_SMCR_SMS_0 | TIM_SMCR_SMS_1;
    T->ARR = (T == TIM2) ? 0xFFFFFFFFu : 0xFFFFu;
    T->CNT = 0;
    T->CR1 = TIM_CR1_CEN;
  }

  // ESC: TIM17 CH1 (PB9) a 299.8 kHz; el DMA escribe CCR1 en cada actualización (DShot300)
  configurar(pin2::ESC_SEN, ALTERNA, 0, 2);
  TIM17->PSC = 0;
  TIM17->ARR = DSHOT_ARR;
  TIM17->CCMR1 = pwm1 | TIM_CCMR1_OC1PE;
  TIM17->CCR1 = 0;
  TIM17->CCER = TIM_CCER_CC1E;
  TIM17->BDTR = TIM_BDTR_MOE;
  TIM17->DIER = TIM_DIER_UDE;
  TIM17->CR1 = TIM_CR1_ARPE;
  TIM17->EGR = TIM_EGR_UG;
  TIM17->CR1 |= TIM_CR1_CEN;
  DMAMUX1_Channel0->CCR = DMAMUX_TIM17_UP << DMAMUX_CxCR_DMAREQ_ID_Pos;   // DMA1 canal 1 <- TIM17_UP
  DMA1_Channel1->CPAR = reinterpret_cast<uint32_t>(&TIM17->CCR1);
  DMA1_Channel1->CCR = DMA_CCR_DIR | DMA_CCR_MINC | DMA_CCR_PSIZE_1 | DMA_CCR_MSIZE_1 | DMA_CCR_PL_1;

  // zumbador: TIM16 CH1 (PB8) a 1 MHz de base
  configurar(pin2::ZUMB, ALTERNA, 0, 1);
  TIM16->PSC = F_CPU / 1000000u - 1u;
  TIM16->ARR = 249;
  TIM16->CCMR1 = pwm1 | TIM_CCMR1_OC1PE;
  TIM16->CCR1 = 0;
  TIM16->CCER = TIM_CCER_CC1E;
  TIM16->BDTR = TIM_BDTR_MOE;
  TIM16->CR1 = TIM_CR1_ARPE | TIM_CR1_CEN;

  // ciclo de control: TIM6 a 1 kHz
  TIM6->PSC = F_CPU / 1000000u - 1u;
  TIM6->ARR = 999;
  TIM6->DIER = TIM_DIER_UIE;
  TIM6->CR1 = TIM_CR1_CEN;
  NVIC_SetPriority(TIM6_DAC_IRQn, 2);
  NVIC_EnableIRQ(TIM6_DAC_IRQn);

  // ADC
  for (const pin2::Analogica& a : {pin2::SENS_A, pin2::SENS_B, pin2::VBAT_MED, pin2::IPROPI_I, pin2::IPROPI_D})
    configurar(a.puerto, a.num, ANALOGICA);
  ADC12_COMMON->CCR = (3u << ADC_CCR_CKMODE_Pos);
  adc_iniciar(ADC1);
  adc_iniciar(ADC2);

  i2c_iniciar();
}

uint32_t ms() { return g_ms; }
uint32_t ciclos() { return DWT->CYCCNT; }

void espera_us(uint32_t us) {
  const uint32_t t0 = DWT->CYCCNT, n = us * (F_CPU / 1000000u);
  while (DWT->CYCCNT - t0 < n) {}
}

bool tick_control() {
  if (!g_tick) return false;
  g_tick = false;
  return true;
}

void leer_barra(uint16_t* ambiente, uint16_t* encendido, uint32_t t_emisor_us) {
  escribir(pin2::EMIT, false);
  barrido(ambiente);                                             // luz ambiente
  escribir(pin2::EMIT, true);
  espera_us(t_emisor_us);                                        // establecimiento de los fototransistores
  barrido(encendido);
  escribir(pin2::EMIT, false);
}

float v_bateria() {
  adc_arrancar(ADC1, pin2::VBAT_MED.canal);
  return adc_esperar(ADC1) * (3.3f / 4095.0f) * cfg2::DIV_BATERIA;   // VDDA = 3.3 V del regulador [S]
}

void corrientes(float* i_izq, float* i_der) {
  adc_arrancar(ADC1, pin2::IPROPI_I.canal);
  adc_arrancar(ADC2, pin2::IPROPI_D.canal);
  *i_izq = adc_esperar(ADC1) * (3.3f / 4095.0f) / cfg2::V_IPROPI_POR_A;
  *i_der = adc_esperar(ADC2) * (3.3f / 4095.0f) / cfg2::V_IPROPI_POR_A;
}

void motores(float izq, float der, bool despierto, bool frenar) {
  if (!despierto) {
    TIM1->CCR2 = TIM1->CCR3 = 0;
    escribir(pin2::DRV_nSLEEP, false);                           // salidas en alta impedancia (rueda libre)
    return;
  }
  escribir(pin2::DRV_nSLEEP, true);
  if (frenar) { TIM1->CCR2 = TIM1->CCR3 = 0; return; }
  puente(TIM1->CCR3, pin2::PH_I, izq);
  puente(TIM1->CCR2, pin2::PH_D, der);
}

bool nfault() { return !leer(pin2::DRV_nFAULT); }

int32_t encoder_izq() {
  static uint16_t ultimo = 0;
  static int32_t acumulado = 0;
  const uint16_t c = uint16_t(TIM4->CNT);
  acumulado += int16_t(c - ultimo);                              // extiende a 32 bits
  ultimo = c;
  return acumulado;
}

int32_t encoder_der() { return int32_t(TIM2->CNT); }

bool i2c_escribir(uint8_t dir7, uint8_t reg, uint8_t valor) {
  I2C3->ICR = I2C_ICR_STOPCF | I2C_ICR_NACKCF;
  I2C3->CR2 = (uint32_t(dir7) << 1) | (2u << I2C_CR2_NBYTES_Pos) | I2C_CR2_AUTOEND | I2C_CR2_START;
  if (!i2c_esperar(I2C_ISR_TXIS)) return false;
  I2C3->TXDR = reg;
  if (!i2c_esperar(I2C_ISR_TXIS)) return false;
  I2C3->TXDR = valor;
  if (!i2c_esperar(I2C_ISR_STOPF)) return false;
  I2C3->ICR = I2C_ICR_STOPCF;
  return true;
}

bool i2c_leer(uint8_t dir7, uint8_t reg, uint8_t* datos, uint32_t n) {
  if (n == 0 || n > 255) return false;
  I2C3->ICR = I2C_ICR_STOPCF | I2C_ICR_NACKCF;
  I2C3->CR2 = (uint32_t(dir7) << 1) | (1u << I2C_CR2_NBYTES_Pos) | I2C_CR2_START;
  if (!i2c_esperar(I2C_ISR_TXIS)) return false;
  I2C3->TXDR = reg;
  if (!i2c_esperar(I2C_ISR_TC)) return false;
  I2C3->CR2 = (uint32_t(dir7) << 1) | I2C_CR2_RD_WRN | (n << I2C_CR2_NBYTES_Pos) | I2C_CR2_AUTOEND | I2C_CR2_START;
  for (uint32_t i = 0; i < n; ++i) {
    if (!i2c_esperar(I2C_ISR_RXNE)) return false;
    datos[i] = uint8_t(I2C3->RXDR);
  }
  if (!i2c_esperar(I2C_ISR_STOPF)) return false;
  I2C3->ICR = I2C_ICR_STOPCF;
  return true;
}

uint16_t dshot_trama(uint16_t valor, bool telemetria) {
  if (valor > 2047) valor = 2047;
  const uint16_t v = uint16_t((valor << 1) | (telemetria ? 1u : 0u));
  const uint16_t crc = (v ^ (v >> 4) ^ (v >> 8)) & 0x0Fu;
  return uint16_t((v << 4) | crc);
}

void esc_dshot(uint16_t valor) {
  if ((DMA1_Channel1->CCR & DMA_CCR_EN) && DMA1_Channel1->CNDTR != 0) return;   // la trama anterior aún sale
  const uint16_t t = dshot_trama(valor, false);
  for (int i = 0; i < 16; ++i) g_dshot[i] = (t & (0x8000u >> i)) ? DSHOT_T1 : DSHOT_T0;
  g_dshot[16] = g_dshot[17] = 0;                                 // la línea queda en bajo entre tramas
  DMA1_Channel1->CCR &= ~DMA_CCR_EN;
  DMA1->IFCR = DMA_IFCR_CGIF1;
  DMA1_Channel1->CMAR = reinterpret_cast<uint32_t>(g_dshot);
  DMA1_Channel1->CNDTR = 18;
  DMA1_Channel1->CCR |= DMA_CCR_EN;
}

void zumbador(uint16_t hz) {
  if (hz < 100) { TIM16->CCR1 = 0; return; }
  const uint32_t arr = 1000000u / hz - 1u;
  TIM16->ARR = arr;
  TIM16->CCR1 = (arr + 1u) / 2u;
}

void leds(bool verde, bool amarillo, bool rojo, bool succion) {
  escribir(pin2::LED_VERDE, verde);
  escribir(pin2::LED_AMARILLO, amarillo);
  escribir(pin2::LED_ROJO, rojo);
  escribir(pin2::LED_SUCCION, succion == LED_SUCCION_ALTO);
}

bool boton_start() { return !leer(pin2::BTN_START); }
bool boton_cal() { return !leer(pin2::BTN_CAL); }

const void* flash_datos() { return reinterpret_cast<const void*>(FLASH_DIR); }

bool flash_guardar(const void* datos, uint32_t n) {
  if (n % 8 || n > 2048) return false;
  motores(0, 0, false, false);
  __disable_irq();
  FLASH->KEYR = 0x45670123u;
  FLASH->KEYR = 0xCDEF89ABu;
  while (FLASH->SR & FLASH_SR_BSY) {}
  FLASH->SR = 0xFFFFu;
  // doble banco (DBANK = 1, de fábrica): banco 2, página 127 de 2 KB. Banco único: página 127 de 4 KB (0x0807F000;
  // el enlazador deja libres los últimos 4 KB).
  uint32_t cr = (FLASH->CR & ~(FLASH_CR_PNB | FLASH_CR_BKER)) | (127u << FLASH_CR_PNB_Pos) | FLASH_CR_PER;
  if (FLASH->OPTR & FLASH_OPTR_DBANK) cr |= FLASH_CR_BKER;
  FLASH->CR = cr;
  FLASH->CR |= FLASH_CR_STRT;
  while (FLASH->SR & FLASH_SR_BSY) {}
  FLASH->CR &= ~(FLASH_CR_PER | FLASH_CR_BKER);
  bool ok = !(FLASH->SR & 0xFFFAu);
  FLASH->CR |= FLASH_CR_PG;
  const uint32_t* src = static_cast<const uint32_t*>(datos);
  volatile uint32_t* dst = reinterpret_cast<volatile uint32_t*>(FLASH_DIR);
  for (uint32_t i = 0; ok && i < n / 4; i += 2) {
    dst[i] = src[i];
    dst[i + 1] = src[i + 1];
    while (FLASH->SR & FLASH_SR_BSY) {}
    if (FLASH->SR & 0xFFFAu) ok = false;
    FLASH->SR = FLASH_SR_EOP;
  }
  FLASH->CR &= ~FLASH_CR_PG;
  FLASH->CR |= FLASH_CR_LOCK;
  __enable_irq();
  return ok;
}

}  // namespace hw2

// ================================================================== interrupciones
extern "C" void SysTick_Handler() { ++hw2::g_ms; }

extern "C" void TIM6_DAC_IRQHandler() {
  if (TIM6->SR & TIM_SR_UIF) {
    TIM6->SR = ~TIM_SR_UIF;
    hw2::g_tick = true;
  }
}

extern "C" void _init() {}
extern "C" void _fini() {}

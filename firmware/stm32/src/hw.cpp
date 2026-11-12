// Capa de hardware: STM32G431CBT6 a 170 MHz (registros CMSIS). Referencias: RM0440 (manual de referencia
// STM32G4), DS12589 (hoja de datos STM32G431xB), DRV8833 (TI SLVSAR1), funciones alternas verificadas con
// STM32_open_pin_data de ST (ver docs/CALCULOS_ELECTRICOS.md).
#include "hw.h"

#include "../../config_maestra.h"
#include "pines_generados.h"
#include "stm32g4xx.h"

extern "C" uint32_t SystemCoreClock;

namespace hw {
namespace {

volatile uint32_t g_ms = 0;
volatile bool g_tick = false;
constexpr uint32_t PWM_ARR = F_CPU / cfg::F_PWM - 1;          // 8499 a 20 kHz
constexpr uint32_t FLASH_PAGINA = 63;                          // última página de 2 KB (128 KB)
constexpr uint32_t FLASH_DIR = 0x08000000u + FLASH_PAGINA * 2048u;

GPIO_TypeDef* puerto(char p) {
  switch (p) {
    case 'A': return GPIOA;
    case 'B': return GPIOB;
    case 'C': return GPIOC;
    case 'F': return GPIOF;
    default: return GPIOG;
  }
}

enum Modo : uint32_t { ENTRADA = 0, SALIDA = 1, ALTERNA = 2, ANALOGICA = 3 };

void configurar(const pin::Gpio& g, Modo m, uint32_t pupd = 0, uint32_t velocidad = 1) {
  GPIO_TypeDef* P = puerto(g.puerto);
  const uint32_t n = g.num;
  P->MODER = (P->MODER & ~(3u << (2 * n))) | (uint32_t(m) << (2 * n));
  P->PUPDR = (P->PUPDR & ~(3u << (2 * n))) | (pupd << (2 * n));
  P->OSPEEDR = (P->OSPEEDR & ~(3u << (2 * n))) | (velocidad << (2 * n));
  P->OTYPER &= ~(1u << n);
  if (m == ALTERNA) {
    volatile uint32_t& afr = P->AFR[n >> 3];
    const uint32_t s = 4 * (n & 7);
    afr = (afr & ~(0xFu << s)) | (uint32_t(g.af) << s);
  }
}

inline void escribir(const pin::Gpio& g, bool v) { puerto(g.puerto)->BSRR = v ? (1u << g.num) : (1u << (g.num + 16)); }
inline bool leer(const pin::Gpio& g) { return (puerto(g.puerto)->IDR >> g.num) & 1u; }

// ------------------------------------------------------------------ reloj: HSI16 -> PLL 170 MHz (modo boost)
void reloj() {
  RCC->APB1ENR1 |= RCC_APB1ENR1_PWREN;
  (void)RCC->APB1ENR1;
  PWR->CR5 &= ~PWR_CR5_R1MODE;                                   // rango 1 boost (necesario > 150 MHz)
  FLASH->ACR = (FLASH->ACR & ~FLASH_ACR_LATENCY) | FLASH_ACR_LATENCY_4WS | FLASH_ACR_PRFTEN | FLASH_ACR_ICEN | FLASH_ACR_DCEN;
  while ((FLASH->ACR & FLASH_ACR_LATENCY) != FLASH_ACR_LATENCY_4WS) {}
  RCC->CR |= RCC_CR_HSION;
  while (!(RCC->CR & RCC_CR_HSIRDY)) {}
  RCC->PLLCFGR = RCC_PLLCFGR_PLLSRC_HSI | ((4 - 1) << RCC_PLLCFGR_PLLM_Pos) | (85 << RCC_PLLCFGR_PLLN_Pos) |
                 (0 << RCC_PLLCFGR_PLLR_Pos) | RCC_PLLCFGR_PLLREN;     // 16/4·85/2 = 170 MHz
  RCC->CR |= RCC_CR_PLLON;
  while (!(RCC->CR & RCC_CR_PLLRDY)) {}
  // transición > 80 MHz: AHB/2 durante el cambio de reloj, luego AHB/1 (RM0440 §7.2.7)
  RCC->CFGR = (RCC->CFGR & ~RCC_CFGR_HPRE) | RCC_CFGR_HPRE_DIV2;
  RCC->CFGR = (RCC->CFGR & ~RCC_CFGR_SW) | RCC_CFGR_SW_PLL;
  while ((RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_PLL) {}
  for (volatile int i = 0; i < 200; ++i) {}                      // > 1 µs a 85 MHz
  RCC->CFGR &= ~RCC_CFGR_HPRE;                                   // AHB = APB1 = APB2 = 170 MHz
  SystemCoreClock = F_CPU;
}

// ------------------------------------------------------------------ ADC1 y ADC2 (reloj síncrono HCLK/4 = 42.5 MHz)
void adc_iniciar(ADC_TypeDef* A) {
  A->CR &= ~ADC_CR_DEEPPWD;
  A->CR |= ADC_CR_ADVREGEN;
  espera_us(30);                                                 // tADCVREG_STUP ≤ 20 µs
  A->CR &= ~ADC_CR_ADCALDIF;
  A->CR |= ADC_CR_ADCAL;
  while (A->CR & ADC_CR_ADCAL) {}
  espera_us(2);
  A->ISR = ADC_ISR_ADRDY;
  A->CR |= ADC_CR_ADEN;
  while (!(A->ISR & ADC_ISR_ADRDY)) {}
  A->CFGR = ADC_CFGR_OVRMOD;                                     // 12 bits, alineado a la derecha, disparo por software
  // 47.5 ciclos de muestreo en todos los canales (1.1 µs, fuente de 10 kΩ): código 0b100
  uint32_t s1 = 0, s2 = 0;
  for (int c = 0; c < 10; ++c) s1 |= 4u << (3 * c);
  for (int c = 0; c < 9; ++c) s2 |= 4u << (3 * c);
  A->SMPR1 = s1;
  A->SMPR2 = s2;
}

inline void adc_arrancar(ADC_TypeDef* A, uint32_t canal) {
  A->SQR1 = canal << ADC_SQR1_SQ1_Pos;                           // longitud 1
  A->CR |= ADC_CR_ADSTART;
}

inline uint16_t adc_esperar(ADC_TypeDef* A) {
  while (!(A->ISR & ADC_ISR_EOC)) {}
  return uint16_t(A->DR);
}

// Convierte las dos secuencias en paralelo, un canal por paso en cada ADC.
void barrido(uint16_t* raw, float* v_bat) {
  const int n = pin::ADC1_N > pin::ADC2_N ? pin::ADC1_N : pin::ADC2_N;
  for (int k = 0; k < n; ++k) {
    if (k < pin::ADC1_N) adc_arrancar(ADC1, pin::ADC1_CANAL[k]);
    if (k < pin::ADC2_N) adc_arrancar(ADC2, pin::ADC2_CANAL[k]);
    if (k < pin::ADC1_N) {
      const uint16_t v = adc_esperar(ADC1);
      const int s = pin::ADC1_SENSOR[k];
      if (s >= 0) raw[s] = v; else if (v_bat) *v_bat = v * (3.3f / 4095.0f) * pin::DIVISOR_VBAT;
    }
    if (k < pin::ADC2_N) {
      const uint16_t v = adc_esperar(ADC2);
      const int s = pin::ADC2_SENSOR[k];
      if (s >= 0) raw[s] = v; else if (v_bat) *v_bat = v * (3.3f / 4095.0f) * pin::DIVISOR_VBAT;
    }
  }
}

// ------------------------------------------------------------------ puerto serie con colas
constexpr uint32_t TAM_TX = 1024, TAM_RX = 128;
volatile char tx_buf[TAM_TX];
volatile uint32_t tx_ini = 0, tx_fin = 0;
volatile char rx_buf[TAM_RX];
volatile uint32_t rx_ini = 0, rx_fin = 0;

volatile uint32_t& ccr(int canal) {
  switch (canal) {
    case 1: return TIM1->CCR1;
    case 2: return TIM1->CCR2;
    case 3: return TIM1->CCR3;
    default: return TIM1->CCR4;
  }
}

void puente(volatile uint32_t& in1, volatile uint32_t& in2, float d) {
  const float T = float(PWM_ARR + 1);
  if (d > 1.0f) d = 1.0f;
  if (d < -1.0f) d = -1.0f;
  if (d >= 0.0f) {          // adelante con decaimiento lento: IN1 = 1, IN2 = PWM (alto = freno)
    in1 = PWM_ARR + 1;
    in2 = uint32_t((1.0f - d) * T);
  } else {                  // atrás: IN2 = 1, IN1 = PWM
    in1 = uint32_t((1.0f + d) * T);
    in2 = PWM_ARR + 1;
  }
}

}  // namespace

// ================================================================== público
void iniciar() {
  reloj();
  RCC->AHB2ENR |= RCC_AHB2ENR_GPIOAEN | RCC_AHB2ENR_GPIOBEN | RCC_AHB2ENR_GPIOCEN | RCC_AHB2ENR_GPIOFEN | RCC_AHB2ENR_ADC12EN;
  RCC->APB1ENR1 |= RCC_APB1ENR1_TIM2EN | RCC_APB1ENR1_TIM3EN | RCC_APB1ENR1_TIM6EN;
  RCC->APB2ENR |= RCC_APB2ENR_TIM1EN | RCC_APB2ENR_USART1EN | RCC_APB2ENR_SYSCFGEN;
  (void)RCC->APB2ENR;

  // base de tiempo: SysTick 1 ms y contador de ciclos
  SysTick_Config(F_CPU / 1000);
  DCB->DEMCR |= DCB_DEMCR_TRCENA_Msk;
  DWT->CYCCNT = 0;
  DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;

  // salidas seguras primero: puente H dormido, emisores apagados
  escribir(pin::DRV_SLEEP, false); configurar(pin::DRV_SLEEP, SALIDA);
  escribir(pin::EMIT_G, false); configurar(pin::EMIT_G, SALIDA);
  escribir(pin::LED_OK, false); configurar(pin::LED_OK, SALIDA);
  escribir(pin::LED_ERR, false); configurar(pin::LED_ERR, SALIDA);
  configurar(pin::BTN_START, ENTRADA, 1);                        // pull-up interno, el botón va a GND
  configurar(pin::BTN_CAL, ENTRADA, 1);
  configurar(pin::DRV_FAULT, ENTRADA, 0);                        // pull-up externo R12

  // PWM: TIM1 CH1-CH4 a 20 kHz
  configurar(pin::PWM_AIN1, ALTERNA, 0, 2); configurar(pin::PWM_AIN2, ALTERNA, 0, 2);
  configurar(pin::PWM_BIN1, ALTERNA, 0, 2); configurar(pin::PWM_BIN2, ALTERNA, 0, 2);
  TIM1->PSC = 0;
  TIM1->ARR = PWM_ARR;
  const uint32_t pwm1 = TIM_CCMR1_OC1M_1 | TIM_CCMR1_OC1M_2;     // modo PWM 1 (0110)
  TIM1->CCMR1 = pwm1 | TIM_CCMR1_OC1PE | (pwm1 << 8) | TIM_CCMR1_OC2PE;
  TIM1->CCMR2 = pwm1 | TIM_CCMR2_OC3PE | (pwm1 << 8) | TIM_CCMR2_OC4PE;
  TIM1->CCR1 = TIM1->CCR2 = TIM1->CCR3 = TIM1->CCR4 = PWM_ARR + 1;   // ambos en alto = freno
  TIM1->CCER = TIM_CCER_CC1E | TIM_CCER_CC2E | TIM_CCER_CC3E | TIM_CCER_CC4E;
  TIM1->BDTR = TIM_BDTR_MOE;
  TIM1->CR1 = TIM_CR1_ARPE;
  TIM1->EGR = TIM_EGR_UG;
  TIM1->CR1 |= TIM_CR1_CEN;

  // encoders: TIM2 (izquierdo, 32 bits) y TIM3 (derecho, 16 bits), modo 3 (4 flancos), filtro fDTS/16 N=8
  configurar(pin::ENC_L_A, ALTERNA); configurar(pin::ENC_L_B, ALTERNA);
  configurar(pin::ENC_R_A, ALTERNA); configurar(pin::ENC_R_B, ALTERNA);
  TIM_TypeDef* const encoders[2] = {TIM2, TIM3};
  for (TIM_TypeDef* T : encoders) {
    T->CCMR1 = TIM_CCMR1_CC1S_0 | TIM_CCMR1_CC2S_0 | (0xAu << TIM_CCMR1_IC1F_Pos) | (0xAu << TIM_CCMR1_IC2F_Pos);
    T->CCER = 0;
    T->SMCR = TIM_SMCR_SMS_0 | TIM_SMCR_SMS_1;
    T->ARR = (T == TIM2) ? 0xFFFFFFFFu : 0xFFFFu;
    T->CNT = 0;
    T->CR1 = TIM_CR1_CEN;
  }

  // periodo de control: TIM6 a 1 kHz
  TIM6->PSC = F_CPU / 1000000 - 1;
  TIM6->ARR = cfg::PERIODO_MIN_US - 1;
  TIM6->DIER = TIM_DIER_UIE;
  TIM6->CR1 = TIM_CR1_CEN;
  NVIC_SetPriority(TIM6_DAC_IRQn, 2);
  NVIC_EnableIRQ(TIM6_DAC_IRQn);

  // ADC
  for (int k = 0; k < pin::ADC1_N; ++k) configurar(pin::ADC1_PIN[k], ANALOGICA);
  for (int k = 0; k < pin::ADC2_N; ++k) configurar(pin::ADC2_PIN[k], ANALOGICA);
  ADC12_COMMON->CCR = (3u << ADC_CCR_CKMODE_Pos);                // HCLK/4
  adc_iniciar(ADC1);
  adc_iniciar(ADC2);

  // USART1 a 115200 8N1 (puerto serie virtual del STLINK-V3MINIE)
  configurar(pin::UART_TX, ALTERNA, 0, 1);
  configurar(pin::UART_RX, ALTERNA, 1, 1);
  USART1->BRR = (F_CPU + cfg::UART_BAUDIOS / 2) / cfg::UART_BAUDIOS;
  USART1->CR1 = USART_CR1_TE | USART_CR1_RE | USART_CR1_RXNEIE_RXFNEIE | USART_CR1_UE;
  NVIC_SetPriority(USART1_IRQn, 3);
  NVIC_EnableIRQ(USART1_IRQn);
}

uint32_t ms() { return g_ms; }
uint32_t ciclos() { return DWT->CYCCNT; }

void espera_us(uint32_t us) {
  const uint32_t t0 = DWT->CYCCNT, n = us * (F_CPU / 1000000);
  while (DWT->CYCCNT - t0 < n) {}
}

bool tick_control() {
  if (!g_tick) return false;
  g_tick = false;
  return true;
}

void emisores(bool on) { escribir(pin::EMIT_G, on); }

void leer_sensores(uint16_t* apagado, uint16_t* encendido, float* v_bat, bool resta, uint32_t t_emisor_us) {
  if (resta) {
    emisores(false);
    barrido(apagado, v_bat);                                     // luz ambiente (y batería)
    emisores(true);
    espera_us(t_emisor_us);                                      // establecimiento del fototransistor
    barrido(encendido, nullptr);
    emisores(false);
  } else {
    emisores(true);
    barrido(encendido, v_bat);
    for (int i = 0; i < cfg::N_SENSORES; ++i) apagado[i] = 4095;
  }
}

void motores(float izq, float der) {
  if (cfg::INVERTIR_MOTOR_IZQ) izq = -izq;
  if (cfg::INVERTIR_MOTOR_DER) der = -der;
  puente(ccr(pin::CANAL_AIN1), ccr(pin::CANAL_AIN2), izq);       // AOUT -> motor izquierdo (J2)
  puente(ccr(pin::CANAL_BIN1), ccr(pin::CANAL_BIN2), der);       // BOUT -> motor derecho (J3)
  escribir(pin::DRV_SLEEP, true);
}

void motores_apagar() {
  TIM1->CCR1 = TIM1->CCR2 = TIM1->CCR3 = TIM1->CCR4 = PWM_ARR + 1;
  escribir(pin::DRV_SLEEP, false);
}

bool falla_driver() { return !leer(pin::DRV_FAULT); }

int32_t encoder_izq() {
  const int32_t c = int32_t(TIM2->CNT);
  return cfg::INVERTIR_ENCODER_IZQ ? -c : c;
}

int32_t encoder_der() {
  static uint16_t ultimo = 0;
  static int32_t acumulado = 0;
  const uint16_t c = uint16_t(TIM3->CNT);
  acumulado += int16_t(c - ultimo);                              // extiende a 32 bits
  ultimo = c;
  return cfg::INVERTIR_ENCODER_DER ? -acumulado : acumulado;
}

bool boton_start() { return !leer(pin::BTN_START); }
bool boton_cal() { return !leer(pin::BTN_CAL); }
void led_ok(bool on) { escribir(pin::LED_OK, on); }
void led_error(bool on) { escribir(pin::LED_ERR, on); }

void serie_escribir(const char* s, uint32_t n) {
  for (uint32_t i = 0; i < n; ++i) {
    const uint32_t sig = (tx_fin + 1) % TAM_TX;
    if (sig == tx_ini) break;                                    // cola llena: se descarta (no bloquea el control)
    tx_buf[tx_fin] = s[i];
    tx_fin = sig;
  }
  USART1->CR1 |= USART_CR1_TXEIE_TXFNFIE;
}

void serie_escribir(const char* s) {
  uint32_t n = 0;
  while (s[n]) ++n;
  serie_escribir(s, n);
}

int serie_leer() {
  if (rx_ini == rx_fin) return -1;
  const char c = rx_buf[rx_ini];
  rx_ini = (rx_ini + 1) % TAM_RX;
  return (unsigned char)c;
}

const void* flash_datos() { return reinterpret_cast<const void*>(FLASH_DIR); }

bool flash_guardar(const void* datos, uint32_t n) {
  if (n % 8 || n > 2048) return false;
  motores_apagar();
  __disable_irq();
  FLASH->KEYR = 0x45670123u;
  FLASH->KEYR = 0xCDEF89ABu;
  while (FLASH->SR & FLASH_SR_BSY) {}
  FLASH->SR = 0xFFFFu;                                           // limpia banderas de error
  FLASH->CR = (FLASH->CR & ~FLASH_CR_PNB) | (FLASH_PAGINA << FLASH_CR_PNB_Pos) | FLASH_CR_PER;
  FLASH->CR |= FLASH_CR_STRT;
  while (FLASH->SR & FLASH_SR_BSY) {}
  FLASH->CR &= ~FLASH_CR_PER;
  bool ok = !(FLASH->SR & 0xFFFAu);
  FLASH->CR |= FLASH_CR_PG;
  const uint32_t* src = static_cast<const uint32_t*>(datos);
  volatile uint32_t* dst = reinterpret_cast<volatile uint32_t*>(FLASH_DIR);
  for (uint32_t i = 0; ok && i < n / 4; i += 2) {
    dst[i] = src[i];
    dst[i + 1] = src[i + 1];                                     // doble palabra (64 bits)
    while (FLASH->SR & FLASH_SR_BSY) {}
    if (FLASH->SR & 0xFFFAu) ok = false;
    FLASH->SR = FLASH_SR_EOP;
  }
  FLASH->CR &= ~FLASH_CR_PG;
  FLASH->CR |= FLASH_CR_LOCK;
  __enable_irq();
  return ok;
}

}  // namespace hw

// ================================================================== interrupciones
extern "C" void SysTick_Handler() { ++hw::g_ms; }

extern "C" void TIM6_DAC_IRQHandler() {
  if (TIM6->SR & TIM_SR_UIF) {
    TIM6->SR = ~TIM_SR_UIF;
    hw::g_tick = true;
  }
}

extern "C" void USART1_IRQHandler() {
  using namespace hw;
  const uint32_t isr = USART1->ISR;
  if (isr & USART_ISR_RXNE_RXFNE) {
    const char c = char(USART1->RDR);
    const uint32_t sig = (rx_fin + 1) % TAM_RX;
    if (sig != rx_ini) { rx_buf[rx_fin] = c; rx_fin = sig; }
  }
  if (isr & USART_ISR_ORE) USART1->ICR = USART_ICR_ORECF;
  if ((USART1->CR1 & USART_CR1_TXEIE_TXFNFIE) && (isr & USART_ISR_TXE_TXFNF)) {
    if (tx_ini != tx_fin) {
      USART1->TDR = uint8_t(tx_buf[tx_ini]);
      tx_ini = (tx_ini + 1) % TAM_TX;
    } else {
      USART1->CR1 &= ~USART_CR1_TXEIE_TXFNFIE;
    }
  }
}

// __libc_init_array (newlib) llama a _init; sin crti.o (-nostartfiles) basta una función vacía.
extern "C" void _init() {}
extern "C" void _fini() {}

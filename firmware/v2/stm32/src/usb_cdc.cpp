// V2 · USB CDC ACM mínimo (ver usb_cdc.h).
#include "usb_cdc.h"

#include "stm32g4xx.h"

namespace usb {
namespace {

// ------------------------------------------------------------------ descriptores
// VID 0x0483 / PID 0x5740: los del puerto COM virtual de ST (los usan sus ejemplos de CDC) [S]
const uint8_t DISPOSITIVO[18] = {18, 1, 0x00, 0x02, 0x02, 0x00, 0x00, 64, 0x83, 0x04, 0x40, 0x57, 0x00, 0x02, 1, 2, 3, 1};
const uint8_t CONFIGURACION[67] = {
    9, 2, 67, 0, 2, 1, 0, 0x80, 50,                       // configuración: 2 interfaces, bus, 100 mA
    9, 4, 0, 0, 1, 0x02, 0x02, 0x01, 0,                   // interfaz 0: comunicaciones (CDC ACM)
    5, 0x24, 0x00, 0x10, 0x01,                            // encabezado CDC 1.10
    5, 0x24, 0x01, 0x00, 1,                               // manejo de llamadas
    4, 0x24, 0x02, 0x02,                                  // ACM: SET_LINE_CODING, SET_CONTROL_LINE_STATE
    5, 0x24, 0x06, 0, 1,                                  // unión: maestra 0, esclava 1
    7, 5, 0x82, 0x03, 8, 0, 16,                           // EP2 IN de interrupción, 8 bytes, 16 ms
    9, 4, 1, 0, 2, 0x0A, 0x00, 0x00, 0,                   // interfaz 1: datos
    7, 5, 0x01, 0x02, 64, 0, 0,                           // EP1 OUT bulk
    7, 5, 0x81, 0x02, 64, 0, 0};                          // EP1 IN bulk
const uint8_t IDIOMA[4] = {4, 3, 0x09, 0x04};
const char* const TEXTOS[3] = {"Circuit Forge", "Speed Follower V2", "CFV2-0001"};

// ------------------------------------------------------------------ memoria de paquetes (PMA de 1 KB, acceso de 16 bits)
constexpr uint16_t EP0_TX = 0x40, EP0_RX = 0x80, EP1_TX = 0xC0, EP1_RX = 0x100, EP2_TX = 0x140;
constexpr uint16_t CNT_RX_64 = 0x8000u | (1u << 10);      // BL_SIZE = 1, NUM_BLOCK = 1 -> 64 bytes

inline volatile uint16_t* pma(uint16_t off) { return reinterpret_cast<volatile uint16_t*>(USB_PMAADDR + off); }
inline volatile uint16_t* bt(uint8_t ep, uint8_t k) { return pma(uint16_t(USB->BTABLE + ep * 8 + k)); }  // 0 TX,2 CNT,4 RX,6 CNT
inline volatile uint16_t& epr(uint8_t ep) { return *(&USB->EP0R + ep * 2); }

void pma_escribir(uint16_t off, const uint8_t* d, uint16_t n) {
  for (uint16_t i = 0; i < n; i += 2) *pma(off + i) = uint16_t(d[i] | ((i + 1 < n ? d[i + 1] : 0) << 8));
}
void pma_leer(uint16_t off, uint8_t* d, uint16_t n) {
  for (uint16_t i = 0; i < n; i += 2) {
    const uint16_t w = *pma(off + i);
    d[i] = uint8_t(w);
    if (i + 1 < n) d[i + 1] = uint8_t(w >> 8);
  }
}

// STAT_TX/STAT_RX y DTOG se cambian escribiendo 1 donde se quiere alternar; CTR_RX/CTR_TX se borran escribiendo 0.
void estado_tx(uint8_t ep, uint16_t s) { epr(ep) = uint16_t(((epr(ep) & (USB_EPTX_STAT | USB_EPREG_MASK)) ^ s) | USB_EP_CTR_RX | USB_EP_CTR_TX); }
void estado_rx(uint8_t ep, uint16_t s) { epr(ep) = uint16_t(((epr(ep) & (USB_EPRX_STAT | USB_EPREG_MASK)) ^ s) | USB_EP_CTR_RX | USB_EP_CTR_TX); }
void borrar_ctr_rx(uint8_t ep) { epr(ep) = uint16_t((epr(ep) & 0x7FFFu & USB_EPREG_MASK) | USB_EP_CTR_TX); }
void borrar_ctr_tx(uint8_t ep) { epr(ep) = uint16_t((epr(ep) & 0xFF7Fu & USB_EPREG_MASK) | USB_EP_CTR_RX); }
void poner_ep(uint8_t ep, uint16_t tipo) { epr(ep) = uint16_t(tipo | ep | USB_EP_CTR_RX | USB_EP_CTR_TX); }
void dtog_cero(uint8_t ep) {
  uint16_t v = epr(ep) & USB_EPREG_MASK;
  if (epr(ep) & USB_EP_DTOG_RX) v |= USB_EP_DTOG_RX;
  if (epr(ep) & USB_EP_DTOG_TX) v |= USB_EP_DTOG_TX;
  epr(ep) = uint16_t(v | USB_EP_CTR_RX | USB_EP_CTR_TX);
}

// ------------------------------------------------------------------ estado
volatile bool g_config = false, g_dtr = false;
uint8_t g_dir_pendiente = 0;
const uint8_t* g_ep0_dato = nullptr;
uint16_t g_ep0_resta = 0;
bool g_ep0_zlp = false;
bool g_espera_linea = false;
uint8_t g_linea[7] = {0x00, 0xC2, 0x01, 0x00, 0, 0, 8};      // 115200 8N1 (solo se informa; el USB no tiene baudios)
uint8_t g_buf_txt[64];

constexpr uint32_t TAM_TX = 2048, TAM_RX = 256;
volatile uint8_t tx[TAM_TX], rx[TAM_RX];
volatile uint32_t tx_i = 0, tx_f = 0, rx_i = 0, rx_f = 0;
volatile bool tx_ocupado = false, rx_pausado = false;

void ep0_enviar_trozo() {
  const uint16_t n = g_ep0_resta > 64 ? 64 : g_ep0_resta;
  if (n) pma_escribir(EP0_TX, g_ep0_dato, n);
  *bt(0, 2) = n;
  g_ep0_dato += n;
  g_ep0_resta = uint16_t(g_ep0_resta - n);
  if (n < 64) g_ep0_zlp = false;
  estado_tx(0, USB_EP_TX_VALID);
}

void ep0_responder(const uint8_t* d, uint16_t n, uint16_t pedido) {
  if (n > pedido) n = pedido;
  g_ep0_dato = d;
  g_ep0_resta = n;
  g_ep0_zlp = (n < pedido) && (n % 64 == 0);              // trozo final exacto de 64: hace falta un paquete vacío
  ep0_enviar_trozo();
}

void ep0_cero() { ep0_responder(nullptr, 0, 0); }
void ep0_stall() { estado_tx(0, USB_EP_TX_STALL); estado_rx(0, USB_EP_RX_STALL); }

uint16_t texto(uint8_t i) {
  const char* s = TEXTOS[i - 1];
  uint16_t n = 2;
  for (; *s && n < 62; ++s) { g_buf_txt[n++] = uint8_t(*s); g_buf_txt[n++] = 0; }
  g_buf_txt[0] = uint8_t(n);
  g_buf_txt[1] = 3;
  return n;
}

void tx_arrancar() {                                       // EP1 IN libre: carga hasta 64 bytes de la cola
  if (tx_ocupado || !g_config || tx_i == tx_f) return;
  uint8_t b[64];
  uint16_t n = 0;
  while (n < 64 && tx_i != tx_f) { b[n++] = tx[tx_i]; tx_i = (tx_i + 1) % TAM_TX; }
  pma_escribir(EP1_TX, b, n);
  *bt(1, 2) = n;
  tx_ocupado = true;
  estado_tx(1, USB_EP_TX_VALID);
}

void configurar_datos() {
  poner_ep(1, USB_EP_BULK);
  *bt(1, 0) = EP1_TX; *bt(1, 2) = 0; *bt(1, 4) = EP1_RX; *bt(1, 6) = CNT_RX_64;
  dtog_cero(1);
  estado_tx(1, USB_EP_TX_NAK);
  estado_rx(1, USB_EP_RX_VALID);
  poner_ep(2, USB_EP_INTERRUPT);
  *bt(2, 0) = EP2_TX; *bt(2, 2) = 0;
  dtog_cero(2);
  estado_tx(2, USB_EP_TX_NAK);
  tx_ocupado = false;
  rx_pausado = false;
}

void reinicio_bus() {
  USB->BTABLE = 0;
  poner_ep(0, USB_EP_CONTROL);
  *bt(0, 0) = EP0_TX; *bt(0, 2) = 0; *bt(0, 4) = EP0_RX; *bt(0, 6) = CNT_RX_64;
  estado_tx(0, USB_EP_TX_NAK);
  estado_rx(0, USB_EP_RX_VALID);
  USB->DADDR = USB_DADDR_EF;
  g_config = g_dtr = false;
}

void setup(const uint8_t* s) {
  const uint8_t tipo = s[0], req = s[1];
  const uint16_t valor = uint16_t(s[2] | (s[3] << 8)), largo = uint16_t(s[6] | (s[7] << 8));
  static uint8_t resp[2];
  if ((tipo & 0x60) == 0x00) {                             // estándar
    switch (req) {
      case 6:                                              // GET_DESCRIPTOR
        switch (valor >> 8) {
          case 1: ep0_responder(DISPOSITIVO, sizeof(DISPOSITIVO), largo); return;
          case 2: ep0_responder(CONFIGURACION, sizeof(CONFIGURACION), largo); return;
          case 3: {
            const uint8_t i = uint8_t(valor);
            if (i == 0) { ep0_responder(IDIOMA, sizeof(IDIOMA), largo); return; }
            if (i <= 3) { const uint16_t n = texto(i); ep0_responder(g_buf_txt, n, largo); return; }
            break;
          }
          default: break;
        }
        ep0_stall();
        return;
      case 5: g_dir_pendiente = uint8_t(valor & 0x7F); ep0_cero(); return;            // SET_ADDRESS
      case 9: configurar_datos(); g_config = (valor != 0); ep0_cero(); return;        // SET_CONFIGURATION
      case 8: resp[0] = g_config ? 1 : 0; ep0_responder(resp, 1, largo); return;      // GET_CONFIGURATION
      case 0: resp[0] = resp[1] = 0; ep0_responder(resp, 2, largo); return;           // GET_STATUS
      case 1: case 3: case 11: ep0_cero(); return;          // CLEAR/SET_FEATURE, SET_INTERFACE
      case 10: resp[0] = 0; ep0_responder(resp, 1, largo); return;                    // GET_INTERFACE
      default: ep0_stall(); return;
    }
  }
  if ((tipo & 0x60) == 0x20) {                             // clase CDC
    switch (req) {
      case 0x20: g_espera_linea = true; estado_rx(0, USB_EP_RX_VALID); return;      // SET_LINE_CODING (7 bytes)
      case 0x21: ep0_responder(g_linea, 7, largo); return;                           // GET_LINE_CODING
      case 0x22: g_dtr = (valor & 1u) != 0; ep0_cero(); return;                      // SET_CONTROL_LINE_STATE
      default: break;
    }
  }
  ep0_stall();
}

void ep0_transferencia(bool salida) {
  if (salida) {                                            // CTR_RX: SETUP o datos OUT
    const bool es_setup = (epr(0) & USB_EP_SETUP) != 0;
    const uint16_t n = *bt(0, 6) & 0x3FFu;
    uint8_t b[64];
    pma_leer(EP0_RX, b, n > 64 ? 64 : n);
    borrar_ctr_rx(0);
    if (es_setup && n >= 8) { g_espera_linea = false; setup(b); }      // setup() deja EP0 listo para la etapa siguiente
    else if (g_espera_linea) {
      for (int i = 0; i < 7 && i < n; ++i) g_linea[i] = b[i];
      g_espera_linea = false;
      ep0_cero();                                          // etapa de estado (IN vacío)
    } else {
      estado_rx(0, USB_EP_RX_VALID);                       // fin de la etapa de estado OUT
    }
  } else {                                                 // CTR_TX: terminó un paquete IN
    borrar_ctr_tx(0);
    if (g_dir_pendiente) { USB->DADDR = uint16_t(USB_DADDR_EF | g_dir_pendiente); g_dir_pendiente = 0; }
    if (g_ep0_resta || g_ep0_zlp) ep0_enviar_trozo();
    else estado_rx(0, USB_EP_RX_VALID);
  }
}

}  // namespace

void iniciar() {
  RCC->APB1ENR1 |= RCC_APB1ENR1_USBEN;
  (void)RCC->APB1ENR1;
  USB->CNTR = USB_CNTR_FRES;                               // sale de PDWN con el reinicio forzado
  for (volatile int i = 0; i < 2000; ++i) {}               // tSTARTUP del transceptor (≈ 1 µs)
  USB->CNTR = 0;
  USB->ISTR = 0;
  reinicio_bus();
  USB->CNTR = USB_CNTR_CTRM | USB_CNTR_RESETM | USB_CNTR_SUSPM | USB_CNTR_WKUPM;
  USB->BCDR |= USB_BCDR_DPPU;                              // pull-up interno de DP: el anfitrión nos ve
  NVIC_SetPriority(USB_LP_IRQn, 3);
  NVIC_EnableIRQ(USB_LP_IRQn);
}

bool conectado() { return g_config && g_dtr; }

uint32_t escribir(const char* s, uint32_t n) {
  if (!g_config) return 0;
  uint32_t k = 0;
  for (; k < n; ++k) {
    const uint32_t sig = (tx_f + 1) % TAM_TX;
    if (sig == tx_i) break;                                // cola llena: no se bloquea el ciclo de control
    tx[tx_f] = uint8_t(s[k]);
    tx_f = sig;
  }
  NVIC_DisableIRQ(USB_LP_IRQn);
  tx_arrancar();
  NVIC_EnableIRQ(USB_LP_IRQn);
  return k;
}

void escribir(const char* s) {
  uint32_t n = 0;
  while (s[n]) ++n;
  escribir(s, n);
}

int leer() {
  if (rx_i == rx_f) return -1;
  const uint8_t c = rx[rx_i];
  rx_i = (rx_i + 1) % TAM_RX;
  if (rx_pausado && ((rx_i - rx_f - 1 + TAM_RX) % TAM_RX) >= 64) {   // hay lugar otra vez: acepta paquetes
    NVIC_DisableIRQ(USB_LP_IRQn);
    rx_pausado = false;
    estado_rx(1, USB_EP_RX_VALID);
    NVIC_EnableIRQ(USB_LP_IRQn);
  }
  return c;
}

}  // namespace usb

extern "C" void USB_LP_IRQHandler() {
  using namespace usb;
  uint16_t istr = USB->ISTR;
  if (istr & USB_ISTR_RESET) { USB->ISTR = uint16_t(~USB_ISTR_RESET); reinicio_bus(); }
  while ((istr = USB->ISTR) & USB_ISTR_CTR) {
    const uint8_t ep = istr & USB_ISTR_EP_ID;
    const uint16_t r = epr(ep);
    if (ep == 0) {
      if (r & USB_EP_CTR_RX) ep0_transferencia(true);
      if (epr(0) & USB_EP_CTR_TX) ep0_transferencia(false);
    } else if (ep == 1) {
      if (r & USB_EP_CTR_RX) {
        const uint16_t n = *bt(1, 6) & 0x3FFu;
        uint8_t b[64];
        pma_leer(EP1_RX, b, n > 64 ? 64 : n);
        borrar_ctr_rx(1);
        for (uint16_t i = 0; i < n && i < 64; ++i) {
          const uint32_t sig = (rx_f + 1) % TAM_RX;
          if (sig == rx_i) break;
          rx[rx_f] = b[i];
          rx_f = sig;
        }
        if (((rx_i - rx_f - 1 + TAM_RX) % TAM_RX) >= 64) estado_rx(1, USB_EP_RX_VALID);
        else rx_pausado = true;                            // queda en NAK hasta que leer() libere lugar
      }
      if (epr(1) & USB_EP_CTR_TX) { borrar_ctr_tx(1); tx_ocupado = false; tx_arrancar(); }
    } else {
      if (r & USB_EP_CTR_TX) borrar_ctr_tx(ep);
      if (r & USB_EP_CTR_RX) borrar_ctr_rx(ep);
    }
  }
  if (istr & USB_ISTR_SUSP) USB->ISTR = uint16_t(~USB_ISTR_SUSP);
  if (istr & USB_ISTR_WKUP) USB->ISTR = uint16_t(~USB_ISTR_WKUP);
  if (istr & USB_ISTR_ERR) USB->ISTR = uint16_t(~USB_ISTR_ERR);
}

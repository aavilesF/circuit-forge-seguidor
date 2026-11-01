// Capa de hardware del Speed Follower (ESP32, Arduino). La lógica no depende de este archivo.
#pragma once
#include <Arduino.h>
#include "pines_sf.h"

namespace hw {
void iniciar();
// ciclo con signo -1..1 relativo a la batería. Modo de decaimiento lento (freno corto en el "apagado").
void motores(float izq, float der);
void motores_apagar();
void leer_lecturas(float* lect, int* crudo_on);   // lect: 0 blanco, 1 negro tras calibrar (ver .ino)
void leer_crudo(int* raw);
void leer_reflectancia(float* refl, int* raw_on);
bool boton_start();
bool boton_cal();
void led(bool e);
float voltaje_bateria();
}

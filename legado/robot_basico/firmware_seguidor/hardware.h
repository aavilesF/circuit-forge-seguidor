// Capa de hardware del ESP32 (Arduino). Todo lo que toca pines vive aquí.
// La lógica (posición, PID, control) no sabe nada de esto.
#pragma once
#include <Arduino.h>
#include "parametros.h"
#include "posicion.h"

namespace hw {

void iniciar();

// ---- Motores: cmd de -1 a 1 (negativo = reversa) -----
void motores(float izq, float der);
void motores_apagar();      // STBY a bajo: los motores quedan libres

// ---- Sensores -----
// Lee los n sensores. Si RESTA_AMBIENTE, mide con emisores encendidos y apagados.
// Devuelve la reflectancia en cuentas ADC (más grande = más claro).
// raw_on (opcional): lecturas crudas con emisores encendidos, para detectar fallas.
void leer_reflectancia(float* refl, int* raw_on = nullptr);
// Lectura cruda con emisores encendidos (para diagnóstico).
void leer_crudo(int* raw);

// ---- Interfaz -----
bool boton_start();         // true mientras está presionado
bool boton_cal();
void led(bool encendido);
float perfil_velocidad();   // 0..1 según la perilla
float voltaje_bateria();    // en volts

}  // namespace hw

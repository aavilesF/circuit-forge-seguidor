// Lógica V1 (firmware/seguidor/posicion.h, rama main), sin cambios; probada en PC.
// Calibración de sensores y estimación de la posición de la línea.
// C++ puro: se prueba en la computadora y lo usa el simulador.
#pragma once
#include "parametros.h"

namespace posicion {

// Posición de cada sensor en el marco del robot (mm).
// x: lateral, positivo a la derecha. y: distancia hacia adelante desde el eje de las ruedas.
struct Geometria {
  int   n;
  float x[par::MAX_SENSORES];
  float y[par::MAX_SENSORES];
};

// Barra recta: n sensores separados paso_mm, centrados en el robot.
Geometria geometria_recta(int n, float paso_mm, float dist_eje_mm);

// Arreglo curvo: n sensores sobre un arco de radio radio_mm, separados paso_arco_mm a lo
// largo del arco. El sensor central queda a dist_eje_mm del eje y los extremos más atrás.
Geometria geometria_arco(int n, float paso_arco_mm, float radio_mm, float dist_eje_mm);

// ---- De cuentas ADC a reflectancia ---------------------------------------
struct ModoSensor {
  bool resta_ambiente;   // true: se lee con emisores encendidos y apagados y se restan
  bool luz_baja_voltaje; // true: más luz reflejada = menos voltaje (fototransistor con pull-up, como el TCRT5000 de este robot)
  int  adc_max;
};

// Devuelve la reflectancia en cuentas: más grande = superficie más clara.
// raw_off se ignora si resta_ambiente es false.
float reflectancia(const ModoSensor& modo, int raw_on, int raw_off);

// ---- Calibración -----------------------------------------------------------
// Se barre el arreglo sobre blanco y negro y se guarda el mínimo y el máximo de cada sensor.
struct Calibracion {
  int   n;
  float minimo[par::MAX_SENSORES];
  float maximo[par::MAX_SENSORES];

  void reiniciar(int n_sensores);
  void muestrear(const float* refl);          // actualiza mínimos y máximos
  bool lista(float rango_minimo) const;       // todos los sensores vieron blanco y negro
};

// Oscuridad normalizada: 0 = blanco, 1 = negro (la línea).
void normalizar(const Calibracion& cal, const float* refl, float* oscuridad);

// ---- Posición de la línea --------------------------------------------------
struct Estimacion {
  float pos_mm;        // posición lateral de la línea respecto al centro; + si está a la derecha
  float confianza;     // suma de oscuridad útil (0 si no se ve nada)
  bool  linea_visible;
};

// Promedio ponderado de la posición de los sensores por su oscuridad.
Estimacion estimar_posicion(const Geometria& g, const float* oscuridad,
                            float umbral_ruido, float confianza_min);

}  // namespace posicion

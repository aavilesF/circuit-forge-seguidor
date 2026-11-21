// Robot de emergencia · constantes fijas que comparten la lógica, las pruebas en PC y el firmware (sin Arduino).
// Los nombres vienen de la lógica V1 (firmware/seguidor, rama main) para usar posicion/pid sin cambios.
// Lo que depende del montaje real NO está aquí: está en `Ajustes` (consola `set`) con su valor inicial en config.h.
#pragma once

namespace par {

constexpr int   MAX_SENSORES       = 16;      // capacidad de los arreglos; en uso NUM_SENSORES = 6 (C0..C5)
constexpr float LARGO_MAX_MM       = 200.0f;  // reglamento
constexpr float ANCHO_MAX_MM       = 100.0f;
constexpr float ANCHO_LINEA_MM     = 25.0f;
constexpr float HUECO_MAX_MM       = 5.0f;

constexpr unsigned long PERIODO_CONTROL_US = 2500;  // 400 Hz (SIG está en el ADC1; 6 canales × 2 lecturas caben)
constexpr unsigned long CICLO_MAX_US       = 25000; // en marcha, un ciclo más largo que esto → ERROR 2 (parada segura)
constexpr unsigned long WDT_MS             = 1000;  // watchdog de hardware: si loop() se cuelga, el ESP32 se reinicia
                                                    // (y el DRV8833 queda dormido por su pull-down de nSLEEP)

constexpr int   ADC_MAX            = 4095;    // 12 bits
constexpr float OSCURO_TODOS       = 0.70f;   // oscuridad para contar un sensor como "negro" al detectar robot levantado

}  // namespace par

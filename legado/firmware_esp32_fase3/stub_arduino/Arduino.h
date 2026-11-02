// STUB mínimo de Arduino/ESP32 SOLO para comprobar sintaxis y tipos en la PC (g++ -fsyntax-only).
// No simula el comportamiento del chip. La compilación real requiere arduino-esp32 / PlatformIO.
#pragma once
#include <stdint.h>
#include <stdio.h>
#include <string>
#include <cstring>
#include <cstdlib>
#define HIGH 1
#define LOW 0
#define INPUT 0
#define OUTPUT 1
#define INPUT_PULLUP 2
#define ADC_11db 3
void pinMode(int, int); void digitalWrite(int, int); int digitalRead(int);
int analogRead(int); uint32_t analogReadMilliVolts(int); void analogReadResolution(int); void analogSetPinAttenuation(int, int);
void delay(unsigned long); void delayMicroseconds(unsigned int); unsigned long millis(); unsigned long micros();
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
bool ledcAttach(int, uint32_t, uint8_t); bool ledcWrite(int, uint32_t);
#else
uint32_t ledcSetup(uint8_t, uint32_t, uint8_t); void ledcAttachPin(int, uint8_t); void ledcWrite(uint8_t, uint32_t);
#endif
class String : public std::string {
 public:
  String() {} String(const char* s) : std::string(s) {} String(const std::string& s) : std::string(s) {}
  void trim() { while (!empty() && isspace((unsigned char)back())) pop_back(); while (!empty() && isspace((unsigned char)front())) erase(0, 1); }
  int indexOf(char c, int from = 0) const { auto p = find(c, from); return p == npos ? -1 : (int)p; }
  String substring(int a) const { return String(substr(a)); }
  String substring(int a, int b) const { return String(substr(a, b - a)); }
  bool startsWith(const char* s) const { return rfind(s, 0) == 0; }
  float toFloat() const { return strtof(c_str(), nullptr); }
  long toInt() const { return strtol(c_str(), nullptr, 10); }
  int length() const { return (int)size(); }
};
struct SerialClass {
  void begin(unsigned long); void println(const char*); void println() {} bool available(); String readStringUntil(char);
  template <typename... A> void printf(const char* f, A... a) { std::printf(f, a...); }
};
extern SerialClass Serial;

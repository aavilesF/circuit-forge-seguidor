#pragma once
#include <stddef.h>
#include <stdint.h>
class Preferences {
 public:
  bool begin(const char*, bool = false); void end();
  size_t putUInt(const char*, uint32_t); uint32_t getUInt(const char*, uint32_t = 0);
  size_t putBytes(const char*, const void*, size_t); size_t getBytes(const char*, void*, size_t); size_t getBytesLength(const char*);
};

// dual_serial.h
#pragma once
#include <Arduino.h>

class Dual_Serial : public Stream
{
public:
  static const uint32_t LOCK_TIMEOUT_MS = 100;

  void begin(uint32_t baud)
  {
    Serial.begin(baud);
    Serial1.begin(baud);
  }

  int available() override
  {
    Stream *s = source();
    return s ? s->available() : 0;
  }

  int peek() override
  {
    Stream *s = source();
    return s ? s->peek() : -1;
  }

  int read() override
  {
    Stream *s = source();
    if (!s) return -1;
    int c = s->read();
    if (c>=0)
    {
      _last_byte_time = millis();
      _current_serial = (c == '\n') ? nullptr : s;
    }
    return c;
  }

  size_t write(uint8_t b) override
  {
    if (Serial) Serial.write(b);
    return Serial1.write(b);
  }

  size_t write(const uint8_t *buf , size_t n) override
  {
    if (Serial) Serial.write(buf , n);
    return Serial1.write(buf , n);
  }

  using Print::write; // Allows other types to be used and directed to the overridden write once converted.

  void flush()
  {
    Serial.flush();
    Serial1.flush();
  }

  operator bool() {return true;}

private:
  Stream *_current_serial = nullptr;
  uint32_t _last_byte_time = 0;

  Stream *source()
  {
    if (_current_serial && (millis() - _last_byte_time > LOCK_TIMEOUT_MS))
    {
      _current_serial = nullptr;
    }
    if (_current_serial) return _current_serial;
    else if (Serial.available()) return &Serial;
    else if (Serial1.available()) return &Serial1;
    else return nullptr;
  }
  
};

extern Dual_Serial Link;
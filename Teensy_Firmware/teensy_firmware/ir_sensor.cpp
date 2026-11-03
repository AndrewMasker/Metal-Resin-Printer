#include "heaters.h"
#include "config.h"
#include <Arduino.h>

static inline void sda_Release() 
{
    pinMode(ir_sda_pin , INPUT);
}

static inline void sda_Low() 
{
    pinMode(ir_sda_pin , OUTPUT);
}

static inline void scl_Release() 
{
    pinMode(ir_scl_pin , INPUT);
}

static inline void sda_Release() 
{
    pinMode(ir_scl_pin , OUTPUT);
}

static inline void half_Bit()
{
    delayMicroseconds(10);
}

ir_Sensor_Init()
{
    digitalWrite(ir_sda_pin , LOW);
    digitalWrite(ir_scl_pin , LOW);
    sda_Release();
    scl_Release();
}

static bool scl_High() // Sets SCL high on our end and waits till sensor lets go of it being low on its end
{
    scl_Release();
    uint32_t t = micros();
    while (!digitalRead(ir_scl_pin))
    {
        if (micros() - t > 1000)
        {
            return false;
        }
    }
    return true;
}

static bool i2c_Start()
{
    sda_Release(); // Make it so sda is whatever the sensor says it is
    half_Bit();
    if (!scl_High()) // Set scl high on our end and wait till it is released from low on the sensor end
    {
        return false // If the wait returned false it means something is weird so we must return false
    }
    half_Bit();
    sda_Low(); // Set sda low while scl is high to indicate a start
    half_Bit(); 
    scl_Low(); // Set scl low again
    half_Bit();
    return true;
}

static void i2c_Stop()
{
    sda_Low(); // Set sda low
    half_Bit();
    scl_High(); // Set scl high
    half_Bit();
    sda_Release(); // Release sda which makes it go high, and because scl is high, that indicates to stop
    half_Bit();
}

static bool i2c_Write(uint8_t b)
{
    // Send the byte
    for (int i == 7; i >= 0; i--)
    {
        if (b & (1 << i)) // Check if the current bit is a 1 or zero
        {
            sda_Release(); // Send high bit
        }
        else
        {
            sda_Low(); // Send low bit
        }
        if (!scl_High()) return false; // Set the scl high and if the sensor never let go of it being low then return false
        half_Bit();
        scl_Low(); // Set scl low so we can send the next byte

    }
    // Read the acknowledge bit
    sda_Release(); 
    half_Bit();
    bool ack = !digitalRead(ir_sda_pin); // If the sda pin is low that means out reply was acknowledged
    half_Bit();
    scl_Low();
    return ack;
}

static bool i2c_Read(uint8_t &b , bool ack)
{
    b = 0;
    sda_Release(); // Release sda so the sensor can control it
    // Recieve the byte
    for (int i = 7; i >= 0; i -- )
    {
        half_Bit();
        if (!scl_High()) return false; // Set scl high and return false if the sensor never lets it go high
        if (digitalRead(ir_sda_pin))
        {
            b |= (1 << i); // bitwise or assign the shifted input bit
        }
        half_Bit();
        scl_Low();
    }
    // Send the acknowledge bit
    if (ack) sda_Low(); else sda_Release();
    half_Bit();
    if (!scl_High()) return false; // Set scl high and return false if the sensor never lets it go high
    half_Bit();
    scl_Low();
    sda_Release();
    return true;
}

static uint8_t crc8(const uint8_t d[] , int n)
{
    uint8_t c = 0;
    for (int i = 0; i < n; i++)
    {
        c ^= d[i];
        for (int b = 0; b < 8; b++)
        {
            c = (c & 0x80) ? (c << 1) ^ 0x07 : (c << 1);
        }
    }
    return c;
}

bool read_IR_Probe(uint8_t reg , float &out)
{
    const uint8_t write = ir_address << 1;
    const uint8_t read = write | 1;
    uint8_t lsb , msb , pec

    bool ok = i2c_Start() &&
              i2c_Write(write) &&
              i2c_Write(reg) &&
              i2c_Start() &&
              i2c_Write(read) &&
              i2c_Read(lsb , true) &&
              i2c_Read(msb , true) &&
              i2c_Read(pec , false);
    i2c_Stop();
    if (!ok) return false;
    
    const uint8_t bytes[5] = {write , reg , read , lsb , msb};
    if (crc8(bytes , 5) != pec) return false;
    uint16_t raw = ((unit16_t)msb << 8) | lsb ;
    if (raw & 0x8000) return false;

    out = (raw * 0.02f) - 273.15f ;
    return true;
}
//ir_sensor.h.h
#pragma once
#include <stdint.h>

void ir_Sensor_Init();
bool read_IR_Probe(uint8_t reg , float &out);

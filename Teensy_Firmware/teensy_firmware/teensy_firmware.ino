//teensy_firmware.ino
#include "commands.h"
#include "steppers.h"
#include "limit_switches.h"
#include "heaters.h"
#include "dual_serial.h"

void setup() {
  // put your setup code here, to run once:
  Link.begin(9600);
  steppers_Init();
  switches_Init();
  heaters_Init();
}

void loop() {
  // put your main code here, to run repeatedly:
  poll_For_Commands();
  steppers_Update();
  pid_Update();
  
  // Serial.print("Chamber at: "); Serial.print(return_Temp(0)); Serial.print(" of  "); Serial.print(return_Setpoint(0)); 
  // Serial.print(", Recoater Heater at: "); Serial.print(return_Temp(1)); Serial.print(" of  "); Serial.print(return_Setpoint(1)); 
  // Serial.print(", Recoater Front: "); Serial.print(return_Temp(2)); Serial.print(" of  "); Serial.println(return_Setpoint(1)); 
}

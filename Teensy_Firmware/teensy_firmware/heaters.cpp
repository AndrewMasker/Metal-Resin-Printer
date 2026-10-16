//heaters.cpp
#include "heaters.h"
#include "config.h"
#include <QuickPID.h>
#include <algorithm>
#include <Arduino.h>

static int last_temp_read_times[num_probes] = {0};
static const int adc_max = resolution_mode_to_adc_max[resolution_mode];
static float temps[num_probes];
static float outputs[num_heaters];
static float setpoints[num_heaters] = {0 , 0};
static int window_start_times[num_heaters] = {0 , 0};

static QuickPID pids[num_heaters] = 
{
  QuickPID(&temps[0] , &outputs[0] , &setpoints[0] , kps[0] , kis[0] , kds[0] , QuickPID::pMode::pOnError , QuickPID::dMode::dOnMeas , QuickPID::iAwMode::iAwClamp , QuickPID::Action::direct) , 
  QuickPID(&temps[1] , &outputs[1] , &setpoints[1] , kps[1] , kis[1] , kds[1] , QuickPID::pMode::pOnError , QuickPID::dMode::dOnMeas , QuickPID::iAwMode::iAwClamp , QuickPID::Action::direct) 
};

void heaters_Init()
{
  analogReadResolution(resolution_mode_to_bits[resolution_mode]);
  analogReadAveraging(averaging_mode_to_n[averaging_mode]);

  for (int i = 0; i < num_heaters; i++)
  {
    pinMode(heater_pins[i] , OUTPUT);

    pids[i].SetOutputLimits(0.0 , 1.0);
    pids[i].SetSampleTimeUs(window_size*1000);
    pids[i].SetMode(QuickPID::Control::automatic);
  }
}

static float read_Thermister(int id)
{
  int raw = analogRead(probe_pins[id]);
  if (raw <= 0) raw = 1;
  if (raw >= adc_max) raw = adc_max - 1;
  float resistance = series_resistance[id] * (float)raw / (float)(adc_max - raw);

  float t = resistance / resistance_nominal[id];
  t = log(t);
  t /= beta[id];
  t += 1.0 / (temp_nominal[id] + 273.15);
  t = 1.0 / t;
  
  return t - 273.15;

}

static void probes_Update()
{
  for (int i = 0; i< num_probes; i++)
  {
    if (millis() - last_temp_read_times[i] >= temp_read_intervals[i])
    {
      temps[i] = read_Thermister(i);
      last_temp_read_times[i] = millis();
    }
    
  }
}

void pid_Update()
{
  unsigned long now_time = millis();
  probes_Update();

  for (int i = 0; i < num_heaters; i++)
  {
    if (pids[i].Compute())
    {
      window_start_times[i] = now_time;
    }

    if ((outputs[i]*window_size > (now_time - window_start_times[i])) && temps[i] < max_temps[i] && temps[i] > min_temps[i])
    {
      digitalWrite(heater_pins[i] , HIGH);
      // Serial.println(outputs[0]);
      // Serial.println("on");
    }
    else
    {
      digitalWrite(heater_pins[i] , LOW);
      // Serial.println(outputs[0]);
      // Serial.println("off");
    }
  }
}

void set_Heater_Setpoint(int id , float setpoint)
{
  setpoints[id] = setpoint;
}

float return_Temp(int id)
{
  return temps[id];
}

float return_Setpoint(int id)
{
  return setpoints[id];
}















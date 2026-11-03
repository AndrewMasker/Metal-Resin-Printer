//heaters.cpp
#include "heaters.h"
#include "config.h"
#include "steppers.h"
#include "ir_sensor.h"
#include <QuickPID.h>
#include <algorithm>
#include <Arduino.h>

static unsigned long last_temp_read_times[num_thermisters] = {0};
static unsigned long last_ir_obj_good_time = 0;
static unsigned long last_ir_attempt_time = 0;
static bool ir_obj_ever_good = false;
static const int adc_max = resolution_mode_to_adc_max[resolution_mode];
static float temps[num_probes];
static float outputs[num_heaters];
static float setpoints[num_heaters] = {0 , 0};
static unsigned long window_start_times[num_heaters] = {0 , 0};

static QuickPID pids[num_heaters] = 
{
  QuickPID(&temps[control_sensors[0]] , &outputs[0] , &setpoints[0] , kps[0] , kis[0] , kds[0] , QuickPID::pMode::pOnError , QuickPID::dMode::dOnMeas , QuickPID::iAwMode::iAwClamp , QuickPID::Action::direct) , 
  QuickPID(&temps[control_sensors[1]] , &outputs[1] , &setpoints[1] , kps[1] , kis[1] , kds[1] , QuickPID::pMode::pOnError , QuickPID::dMode::dOnMeas , QuickPID::iAwMode::iAwClamp , QuickPID::Action::direct) 
};

void heaters_Init()
{
  ir_Sensor_Init();
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
  int raw = analogRead(thermister_pins[id]);
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

static void thermisters_Update()
{
  for (int i = 0; i< num_thermisters; i++)
  {
    if (millis() - last_temp_read_times[i] >= temp_read_intervals[i])
    {
      temps[i] = read_Thermister(i);
      last_temp_read_times[i] = millis();
    }
    
  }
}

static void ir_Update()
{
  unsigned long now_time = millis();
  if ( (! axes_Idle()) || ( (now_time - last_ir_attempt_time) < ir_read_interval) )
  {
    return;
  }
  last_ir_attempt_time = now_time;

  if(read_IR_Probe(ir_obj_addr , temps[ir_obj_id]))
  {
    last_ir_obj_good_time = now_time;
    ir_obj_ever_good = true;
  }
  read_IR_Probe(ir_body_addr , temps[ir_body_id]);
}

void pid_Update()
{
  thermisters_Update();
  ir_Update();
  unsigned long now_time = millis();
  
  bool ir_fresh = ir_obj_ever_good && (now_time - last_ir_obj_good_time) < ir_max_stale_age;

  for (int i = 0; i < num_heaters; i++)
  {
    bool input_ok = (control_sensors[i] != ir_obj_id) || ir_fresh;
    if (pids[i].Compute())
    {
      window_start_times[i] = now_time;
    }

    if ((outputs[i]*window_size > (now_time - window_start_times[i])) && temps[limit_sensor[i]] < limit_max[i] && temps[limit_sensor[i]] > limit_min[i] && input_ok)
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
  if (id < 0 || id >= num_heaters) return;
  setpoints[id] = setpoint;
}

float return_Temp(int id)
{
  if (id < 0 || id >= num_probes) return -10000;
  return temps[id];
}

float return_Setpoint(int id)
{
  return setpoints[id];
}















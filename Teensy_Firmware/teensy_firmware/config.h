// config.h
#pragma once

// MICROSTEPPING PINS AND CONFIGURATION

constexpr int m0 = 9 , m1 = 10 , m2 = 11;
constexpr int microstepping_mode_to_pins[6][3] = 
{
  {0 , 0 , 0} , // Full Step , Mode 0
  {1 , 0 , 0} , // 1/2 Step  , Mode 1
  {0 , 1 , 0} , // 1/4 Step  , Mode 2
  {1 , 1 , 0} , // 1/8 Step  , Mode 3
  {0 , 0 , 1} , // 1/16 Step , Mode 4
  {1 , 1 , 1}   // 1/32 Step , Mode 5
};
constexpr int microstepping_mode_to_steps[6] = {1 , 2 , 4 , 8 , 16 , 32};


// STEPPER MOTOR PINS AND CONFIGURATION

// Reservoir: 0 , Build: 1 , Recoater: 2
constexpr int num_axes = 3;
constexpr int step_pins[3] = {19 , 17 , 15}; // 19 17 15
constexpr int dir_pins[3] = {18 , 16 , 14};
constexpr int leads[3] = {4 , 4 , 8};                     // mm/rot or whatever other unit per rotation
constexpr int steps_per_rotation[3] = {200 , 200 , 200};  // steps/rot (full steps)
constexpr float min_travel[3] = {-1 , -185 , -2};         // mm minimum from being zeroed
constexpr float max_travel[3] = {185 , 1 , 200};              // mm maximum from being zeroed
constexpr int min_pulse_width = 5;                        // us minimum pulse witdth that the teensy can send to the drv8825


// LIMIT SWITCH PINS

// Reservoir: 0 , Build: 1 , Recoater: 2
constexpr int switch_pins[3] = {4 , 5 , 6}; // 1 7 20
constexpr bool normally_open[3] = {false , false , true};
constexpr float homing_fast_speed_fracs[3] = {-1 , 1 , -.2};
constexpr float homing_slow_speed_fracs[3] = {-.1 , .1 , -.1};
constexpr float backoff_dist[3] = {4 , -4 , 4};


// TEMPERATURE PINS AND CONFIGURATION

// Chamber: 0 , Recoater: 1
constexpr int num_heaters = 2;
constexpr int num_probes = 3; // The number of probes must be greater than or equal to the number of heaters. The first ones are assinged to a heater.
constexpr int probe_pins[num_probes] = {22 , 23 , 21};
constexpr int heater_pins[num_heaters] = {3 , 2};
constexpr float kps[num_heaters] = {1 , .1};
constexpr float kis[num_heaters] = {0 , 0};
constexpr float kds[num_heaters] = {1 , 2};
constexpr int window_size = 5000;
constexpr unsigned long temp_read_intervals[num_probes] = {1000 , 1000 , 1000};
constexpr float resistance_nominal[num_probes] = {100000.0 , 100000.0 , 100000.0};
constexpr float temp_nominal[num_probes] = {25.0 , 25.0 , 25.0};
constexpr float beta[num_probes] = {3950.0 , 3950.0 , 3950.0};
constexpr float series_resistance[num_probes] = {50000.0 , 50000.0 , 50000.0};
constexpr int resolution_mode = 0; // 0 --> 8 bits , 1 --> 10 bits , 2 --> 12 bits
constexpr int resolution_mode_to_bits[4] = {8 , 10 , 12};
constexpr int resolution_mode_to_adc_max[4] = {255 , 1023 , 4095};
constexpr int averaging_mode = 1;
constexpr int averaging_mode_to_n[4] = {4 , 8 , 16 , 32};




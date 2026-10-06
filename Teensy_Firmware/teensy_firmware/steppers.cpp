// steppers.cpp
#include "steppers.h"
#include "config.h"
#include "settings.h"
#include "limit_switches.h"
#include "dual_serial.h"
#include <AccelStepper.h>
#include <AccelStepperWithDistance.h>
#include <Arduino.h>

static AccelStepperWithDistance axes[] = 
{
  AccelStepperWithDistance(AccelStepperWithDistance::DRIVER , step_pins[0] , dir_pins[0]) , 
  AccelStepperWithDistance(AccelStepperWithDistance::DRIVER , step_pins[1] , dir_pins[1]) , 
  AccelStepperWithDistance(AccelStepperWithDistance::DRIVER , step_pins[2] , dir_pins[2]) 
};

enum Homing_Phase : uint8_t
{
  NIL ,      // Not homing
  FAST ,     // The fast stage of homing
  BACKOFF ,  // The backing off stage of homing
  SLOW ,     // The slow stage of homing
  OFFSET     // The stage where the offset is added
};

static Homing_Phase homing_phase[num_axes] = {NIL , NIL , NIL};
static bool is_Moving[num_axes] = {false};

static float max_speeds_steps[num_axes];
static float fast_homing_speeds_steps[num_axes];
static float slow_homing_speeds_steps[num_axes];

static int microsteps;

void steppers_Init()
{
  // Initialize Axes
  for (int i = 0; i < num_axes; i++)
  {
    microsteps = microstepping_mode_to_steps[settings.microstepping_mode];

    max_speeds_steps[i] = settings.max_speeds[i] * steps_per_rotation[i] * microsteps / leads[i];
    fast_homing_speeds_steps[i] = homing_fast_speed_fracs[i] * max_speeds_steps[i];
    slow_homing_speeds_steps[i] = homing_slow_speed_fracs[i] * max_speeds_steps[i];

    float max_speed_steps =  max_speeds_steps[i];
    float acceleration_steps = settings.accelerations[i] * steps_per_rotation[i] * microsteps / leads[i];

    axes[i].setMaxSpeed(max_speed_steps);
    axes[i].setAcceleration(acceleration_steps);
    axes[i].setStepsPerRotation(steps_per_rotation[i]);
    axes[i].setMicroStep(microsteps);
    axes[i].setDistancePerRotation(leads[i]);
    axes[i].setMinPulseWidth(min_pulse_width);

    // Serial.print("init "); Serial.print(i);
    // Serial.print(" fast="); Serial.println(fast_homing_speeds_steps[i]);

  }

  // Initialize Microstepping Pins
  pinMode(m0 , OUTPUT);
  pinMode(m1 , OUTPUT);
  pinMode(m2 , OUTPUT);

  const int *microstepping_pins = microstepping_mode_to_pins[settings.microstepping_mode];
  digitalWrite(m0 , microstepping_pins[0]);
  digitalWrite(m1 , microstepping_pins[1]);
  digitalWrite(m2 , microstepping_pins[2]);

}

static void home_One_Stepper_Update(int id)
{

  switch (homing_phase[id])
  {
    case FAST:
      axes[id].setSpeed(fast_homing_speeds_steps[id]);
      if (switch_Pressed(id))
      {
        // Serial.print("fast "); Serial.print(id);
        // Serial.print(" fast="); Serial.println(fast_homing_speeds_steps[id]);
        axes[id].setMaxSpeed(fast_homing_speeds_steps[id]);
        axes[id].moveRelative(backoff_dist[id]);
        homing_phase[id] = BACKOFF;
      }
      else
      {
        axes[id].runSpeed();
      }
      break;

    case BACKOFF:
      if (axes[id].distanceToGo() == 0)
      {
        // Serial.print("backoff "); Serial.print(id);
        // Serial.print(" fast="); Serial.println(fast_homing_speeds_steps[id]);
        axes[id].setSpeed(slow_homing_speeds_steps[id]);
        homing_phase[id] = SLOW;
      }
      else
      {
        axes[id].run();
      }
      break;

    case SLOW:
      if (switch_Pressed(id))
      {
        // Serial.print("slow "); Serial.print(id);
        // Serial.print(" fast="); Serial.println(fast_homing_speeds_steps[id]);
        axes[id].moveRelative(settings.homing_offset_dists[id]);
        axes[id].setMaxSpeed(slow_homing_speeds_steps[id]);
        homing_phase[id] = OFFSET;
      }
      else
      {
        axes[id].runSpeed();
      }
      break;

    case OFFSET:
      if (axes[id].distanceToGo() == 0)
      {
        // Serial.print("offset "); Serial.print(id);
        // Serial.print(" fast="); Serial.println(fast_homing_speeds_steps[id]);
        homing_phase[id] = NIL;
        axes[id].setMaxSpeed(max_speeds_steps[id]);
        axes[id].setCurrentPosition(0);
        Link.print("H"); Link.println(id);
        // Serial.print("Axis "); Serial.print(id); Serial.println(" has been homed.");
      }
      else
      {
        axes[id].run();
      }
      break;

    case NIL:
    default:
      break;

  }
}

void steppers_Update()
{
  for (int i = 0; i < num_axes; i++)
  {
    if (homing_phase[i] != NIL)
    {
      home_One_Stepper_Update(i);
    }
    else
    {
      if (axes[i].distanceToGo() != 0 && is_Moving[i] == false)
      {
        is_Moving[i] = true;
      }
      else if (axes[i].distanceToGo() == 0 && is_Moving[i] == true)
      {
        is_Moving[i] = false;
        Link.print("M"); Link.println(i);
      }
      axes[i].run();
    }
  }
}

static bool is_Out_Of_Bounds(int id , float position)
{
  return !((position >= min_travel[id]) && (position <= max_travel[id]));
}

void move_Stepper_Relative(int id , float move)
{
  if (id < 0 || id >= num_axes || is_Out_Of_Bounds(id , axes[id].getCurrentPositionDistance() + move)) return;
  axes[id].moveRelative(move);
}

void move_Stepper_Absolute(int id , float move)
{
  if (id < 0 || id >= num_axes || is_Out_Of_Bounds(id , move)) return;
  axes[id].moveToDistance(move);
}

void home_Stepper(int id)
{
  if (id < 0 || id >= num_axes) return;
  // Serial.print("home "); Serial.print(id);
  // Serial.print(" fast="); Serial.print(fast_homing_speeds_steps[id]);
  homing_phase[id] = FAST;
}

void move_To_Top(int id)
{
  if (id < 0 || id >= num_axes) return;
  axes[id].moveToDistance(max_travel[id]);
}

float get_Axis_Position(int id)
{
  if (id < 0 || id >= num_axes) return -100000;
  return axes[id].getCurrentPositionDistance();
}

void set_Axis_Position(int id , float pos)
{
  if (id < 0 || id >= num_axes) return;
  axes[id].setCurrentPosition(pos * steps_per_rotation[id] * microsteps / leads[id]);

}




















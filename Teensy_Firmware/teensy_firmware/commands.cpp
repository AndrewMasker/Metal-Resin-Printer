//commands.cpp
#include "commands.h"
#include "steppers.h"
#include "heaters.h"
#include "settings.h"
#include "dual_serial.h"
#include <Arduino.h>

static char buffer[32];
static int length = 0;

static void handle_Command(char *command)
{

  if ((command[0] == 'M') & (command[1] == 'R'))
  {
    int stepper_id = atoi(command + 2);
    char *space = strchr(command , ' ');
    if (space)
    {
      float move = atof(space + 1);
      move_Stepper_Relative(stepper_id , move);
    }
  }

  else if ((command[0] == 'M') & (command[1] == 'A'))
  {
    int stepper_id = atoi(command + 2);
    char *space = strchr(command , ' ');
    if (space)
    {
      float move = atof(space + 1);
      move_Stepper_Absolute(stepper_id , move);
    }
  }

  else if ((command[0] == 'M') & (command[1] == 'T'))
  {
    int stepper_id = atoi(command + 2);
    move_To_Top(stepper_id);
  }

  else if ((command[0] == 'G') & (command[1] == 'P'))
  {
    int stepper_id = atoi(command + 2);
    float pos = get_Axis_Position(stepper_id);
    Link.print("GP"); Link.print(stepper_id); Link.print(" "); Link.println(pos); 
  }

  else if ((command[0] == 'S') & (command[1] == 'P'))
  {
    int stepper_id = atoi(command + 2);
    char *space = strchr(command , ' ');
    if (space)
    {
      float pos = atof(space + 1);
      set_Axis_Position(stepper_id , pos);
    }
  }

  else if ((command[0] == 'S') & (command[1] == 'M') & (command[2] == 'S'))
  {
    int axis_id = atoi(command + 3);
    char *space = strchr(command , ' ');
    if (space)
    {
      float speed = atof(space + 1);
      set_Max_Speed(axis_id , speed);
    }
    steppers_Init();
  }

  else if ((command[0] == 'S') & (command[1] == 'A'))
  {
    int axis_id = atoi(command + 2);
    char *space = strchr(command , ' ');
    if (space)
    {
      float acc = atof(space + 1);
      set_Acceleration(axis_id , acc);
    }
  }

  else if ((command[0] == 'S') & (command[1] == 'M') & (command[2] == 'M'))
  {
    char *space = strchr(command , ' ');
    if (space)
    {
      int mode = atof(space + 1);
      set_Microstepping_Mode(mode);
    }
    steppers_Init();
  }

  else if ((command[0] == 'S') & (command[1] == 'O') & (command[2] == 'D'))
  {
    int axis_id = atoi(command + 3);
    char *space = strchr(command , ' ');
    if (space)
    {
      float dist = atof(space + 1);
      set_Offset_Distance(axis_id , dist);
    }
    steppers_Init();
  }

  else if ((command[0] == 'R') & (command[1] == 'D') & (command[2] == 'S'))
  {
    reset_Default_Settings();
    steppers_Init();
  }

  else if (command[0] == 'H')
  {
    int stepper_id = atoi(command + 1);
    home_Stepper(stepper_id);
    
  }

  else if ((command[0] == 'S') && (command[1] == 'H'))
  {
    int heater_id = atoi(command + 2);
    char *space = strchr(command , ' ');
    if (space)
    {
      float setpoint = atof(space + 1);
      set_Heater_Setpoint(heater_id , setpoint);
    }
  }

  else if ((command[0] == 'G') && (command[1] == 'T'))
  {
    int probe_id = atoi(command + 2);
    float temp = return_Temp(probe_id);
    Link.print("GT"); Link.print(probe_id); Link.print(" "); Link.println(temp);
  }

  else if (command[0] == 'E')
  {
    char *space = strchr(command , ' ');
    if (space)
    {
      Link.println(space + 1);
    }
  }


}

void poll_For_Commands()
{
  while (Link.available())
  {
      char c = Link.read();
      if (c == '\n')
      {
        buffer[length] = 0;
        handle_Command(buffer);
        length = 0;
      }
      else if (length < (int)sizeof(buffer) - 1)
      {
        buffer[length++] = c;
      }
  }
}






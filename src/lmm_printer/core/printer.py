import time
import RPi.GPIO as GPIO
from lmm_printer.core.files import save_Printer_State , load_Printer_State
from lmm_printer.core.types import Printer_State
from lmm_printer.utils.vendored_handling import silence

class Printer:
    def __init__(self , teensy , projector , config):
        self.teensy = teensy
        self.projector = projector
        self.config = config
        self.teensy.start_Thread()
        self.listening_for = []

    def home_Axis(self , axis_id , wait = True , listen = True):
        command = "H" + str(axis_id)
        self.teensy.send_Command(command)
        if listen:
            self.listening_for.append(command)
        if wait:
            self.wait_For_Response()

    def home_Axes(self , ids = None , one_at_a_time = False):
        if ids is None:
            for i in range(3):
                self.home_Axis(i , wait = one_at_a_time)
        else:
            for i in ids:
                self.home_Axis(i , wait = one_at_a_time)
        if not one_at_a_time:
            self.wait_For_Response()

    def move_Axis_Relative(self , axis_id , move , wait = True , listen = True):
        command = "MR" + str(axis_id) + " " + str(move)
        self.teensy.send_Command(command)
        if listen:
            self.listening_for.append("M" + str(axis_id))
        if wait:
            self.wait_For_Response()

    def move_Axis_Absolute(self , axis_id , move , wait = True , listen = True):
        command = "MA" + str(axis_id) + " " + str(move)
        self.teensy.send_Command(command)
        if listen:
            self.listening_for.append("M" + str(axis_id))
        if wait:
            self.wait_For_Response()

    def move_Axis_To_Top(self , axis_id , wait = True , listen = True):
        command = "MT" + str(axis_id)
        self.teensy.send_Command(command)
        if listen:
            self.listening_for.append("M" + str(axis_id))
        if wait:
            self.wait_For_Response()

    def get_Axis_Position(self , axis_id):
        command = "GP" + str(axis_id)
        self.teensy.send_Command(command)
        self.listening_for.append(command)
        response = self.wait_For_Response()[0]
        pos = float(response.split()[-1])
        return pos

    def set_Axis_Position(self , axis_id , position):
        command = "SP" + str(axis_id) + " " + str(position)
        self.teensy.send_Command(command)

    def get_Temp(self , probe_id):
        command = "GT" + str(probe_id)
        self.teensy.send_Command(command)
        self.listening_for.append(command)
        response = self.wait_For_Response()[0]
        temp = float(response.split()[-1])
        return temp

    def set_Heater(self , heater_id , temp):
        command = "SH" + str(heater_id) + " " + str(temp)    
        self.teensy.send_Command(command)
    
    def start_Heaters(self):
        self.set_Heater(0 , self.config["chamber"]["temp"])
        self.set_chamber_temp = self.config["chamber"]["temp"]

        self.set_Heater(1 , self.config["recoater"]["temp"])
        self.set_recoater_temp = self.config["recoater"]["temp"]

    def check_Heaters(self):
        chamber_good = False
        recoater_good = False

        chamber_temp = self.get_Temp(0)
        recoater_temp = self.get_Temp(2)

        if (self.set_chamber_temp != self.config["chamber"]["temp"]) or (self.set_recoater_temp != self.config["recoater"]["temp"]):
            self.start_Heaters()
        
        if self.set_chamber_temp - self.config["chamber"]["valid_diff"] <= chamber_temp <= self.set_chamber_temp + self.config["chamber"]["valid_diff"]:
            chamber_good = True
        if self.set_recoater_temp - self.config["recoater"]["valid_diff"] <= recoater_temp <= self.set_recoater_temp + self.config["recoater"]["valid_diff"]:
            recoater_good = True

        if chamber_good and recoater_good:
            return True
        else:
            return False

    def init_Print(self , image_1 , options):
        with silence():
            self.projector.send_pixeldata_to_buffer(image_1 , 0 , 0)
        self.move_Axis_Relative(1 , -options["layer_thickness"] , wait = False , listen = False)

    def do_Current_Layer(self , next_image , options):                
        self.move_Axis_Relative(0 , self.config["reservoir"]["extrude_multiple"] * options["layer_thickness"] , wait = False , listen = False)
        
        self.move_Axis_To_Top(2)
        self.save_State()

        with silence():
            self.projector.swap_buffer()
            exposure_start_time = time.monotonic()
            self.projector.expose_pattern(exposed_frames = int(60 * options["exposure_time"]))
            if next_image is not None:
                self.projector.send_pixeldata_to_buffer(next_image , 0 , 0)

        while True:
            if time.monotonic() - exposure_start_time > options["exposure_time"]:
                break
        
        self.move_Axis_Relative(1 , -options["layer_thickness"] , wait = False , listen = False)
        self.move_Axis_Absolute(2 , 0)
        self.save_State()

    def do_Current_Layer_Bad(self , next_image , options): # This version of the function causes drift between the actual and tracked postion.       
        self.move_Axis_Relative(0 , self.config["reservoir"]["extrude_multiple"] * options["layer_thickness"] + self.config["recoater"]["vertical_pullback"] , wait = False , listen = False)
        self.move_Axis_Relative(1 , -options["layer_thickness"] , wait = False , listen = False)

        self.move_Axis_To_Top(2)
        self.save_State()

        self.move_Axis_Relative(0 , -self.config["recoater"]["vertical_pullback"] , wait = False , listen = False)
        self.move_Axis_Relative(1 , -self.config["recoater"]["vertical_pullback"] , wait = False , listen = False)

        self.move_Axis_Absolute(2 , 0 , wait = False , listen = False)
        while True:
            recoater_pos = self.get_Axis_Position(2)
            if recoater_pos < self.config["recoater"]["clear_pos"]:
                break

        self.move_Axis_Relative(1 , self.config["recoater"]["vertical_pullback"])
        self.save_State()

        with silence():
            self.projector.swap_buffer()
            exposure_start_time = time.monotonic()
            self.projector.expose_pattern(exposed_frames = int(60 * options["exposure_time"]))
            if next_image is not None:
                self.projector.send_pixeldata_to_buffer(next_image , 0 , 0)

        while True:
            if time.monotonic() - exposure_start_time > options["exposure_time"]:
                break

        self.listening_for.append("M2")
        self.wait_For_Response()

        self.save_State()

    def wait_For_Response(self , timeout = 60):
        return_list = []
        start = time.monotonic()
        while len(self.listening_for) != 0:
            if time.monotonic() - start > timeout:
                pending = list(self.listening_for)
                self.listening_for.clear()
                raise TimeoutError(f"Teensy never responded to one of these: {pending}")
            messages = self.teensy.get_Messages()
            for lf in list(self.listening_for):
                responses = [s for s in messages if lf in s]
                if responses:
                    response = responses[0]
                    while lf in self.listening_for:
                        self.listening_for.remove(lf)
                    return_list.append(response)
            time.sleep(.005)
        return return_list

    def return_Current_State(self):
        pos = []
        for i in range(3):
            pos.append(self.get_Axis_Position(i))

        state = Printer_State()
        state.pos = pos
        return state

    def save_State(self , safe_shutdown = False):
        state = self.return_Current_State()
        state.safe_shutdown = safe_shutdown
        save_Printer_State(self.config["files"]["state_file"] , state)

    def load_State(self):
        state = load_Printer_State(self.config["files"]["state_file"])
        for i in range(3):
            self.set_Axis_Position(i , state.pos[i])

        return state

    def safe_Shutdown(self):
        self.save_State(safe_shutdown = True)
        self.stop_Active()
        self.teensy.shutdown()
        GPIO.cleanup()

    def stop_Active(self):
        with silence():
            self.projector.stop_exposure()
        self.set_Heater(0 , 0)
        self.set_Heater(1 , 0)
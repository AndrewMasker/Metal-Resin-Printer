from lmm_printer.core.types import State , Result

class Print_Session:
    """
    Holds functionality for running a print session.

    Parameters:
        args (dict): A dict of arguments from the command line call.
        config (dict): A dict representation of the config file.

    Attributes:
        args (dict): This print session's arguments.
        config (dict): A representation of this print session's config file.
        file_good (bool): Whether a file has been loaded along with its attributes.
        stop_print (bool): A flag that stops an ongoing print.
        should_go (bool): A flag that tells the print session to continue polling for commands.
        input_handler: An object that inherits from Generic_Input_Handler that handles inputs with specific functions.
        print_input_handler: An object that inherits from Generic_Print_Input_Handler that handles inputs during printing.
        output_handler: An object that inherits from Generic_Output_Handler that handles outputs with specific functions.
        hardware_good (bool): Whether the hardware is properly loaded.
        num_layers (int): The number of layers in the loaded file.
        options (dict): The options loaded from the file.
    """

    def __init__(self , args , config):
        self.args = args
        self.config = config
        self._add_State_File_To_Config()
        self.file_good = False
        self.stop_print = False
        self.should_go = True
        self.hardware_good = False

        if args.gui:
            from lmm_printer.interface.gui.ui import UI
            self.ui = UI()
        else:
            from lmm_printer.interface.cli.ui import UI
            self.ui = UI()

    def notify(self , message):
        self.ui.notify(message)


    def _add_State_File_To_Config(self):
        """
        Adds the state file to the config.
        """

        from platformdirs import user_state_path

        state_dir = user_state_path(self.config["files"]["app_name"] , ensure_exists = True)
        state_file = state_dir / (self.config["files"]["state_file_name"] + ".json")
        self.config["files"]["state_file"] = state_file

    def load_Hardware(self):
        """
        Loads hardware.
        """

        from lmm_printer.teensy.establish import return_Teensy_Serial
        from lmm_printer.projector.establish import return_Projector
        from lmm_printer.core.printer import Printer

        teensy_result = return_Teensy_Serial(self.config["teensy"]["vid"] , self.config["teensy"]["baudrate"] , self.config["teensy"]["timeout"] , self.config["teensy"]["enable_fallback"])
        self.notify(teensy_result)
        if teensy_result.state == State.ERROR:
            teensy_loaded = False
        else:
            teensy_loaded = True
        teensy = teensy_result.value

        projector_result = return_Projector(self.config["projector"]["spi_max_speed"])
        self.notify(projector_result)
        if projector_result.state == State.ERROR:
            projector_loaded = False
        else:
            projector_loaded = True
        projector = projector_result.value

        if teensy_loaded and projector_loaded:
            self.printer = Printer(teensy , projector , self.config)
            state = self.printer.load_State()
            if not state.safe_shutdown:
                self.notify("Last shutdown was not safe. Ensure you home if you do not trust the axes' positions. ")
            else:
                self.notify("Ensure you trust the axes' positions before starting.Home if you do not. ")
            self.hardware_good = True
        else:
            self.hardware_good = False

    def load_Print_File(self , file):
        self.file = file
        self.load_Print_File_Attributes()

    def load_Print_File_Attributes(self):
        """
        Loads the print file attributes.
        """

        from lmm_printer.core.types import Print_File

        if not hasattr(self , "file"):
            self.notify("Choose a file first. ")
            return
        with Print_File(self.file) as print_file:
            num_layers = print_file.get_Num_Layers()
            image_result = print_file.get_Image(1)
            options_result = print_file.get_Options()
        
        print_file_error = False
        if image_result.state == State.ERROR:
            self.notify(image_result)
            print_file_error = True
        if options_result.state == State.ERROR:
            self.notify(options_result)
            print_file_error = True
        if print_file_error:
            return

        self.num_layers = num_layers
        self.options = options_result.value
        self.file_good = True

    def home(self , axes):
        if not self.hardware_good:
            return [Result(state = State.ERROR , message=f"Hardware is not good.")]
        messages = []
        if "all" in axes:
            try:
                self.printer.home_Axes() 
                self.printer.save_State()
                messages.append(Result(value=None , state=State.SUCCESS , message="All axes homed successfully."))
            except Exception as e:
                self.printer.save_State()
                messages.append(Result(value="all error" , state=State.ERROR , message=f"Error homing all axes. Error was: {e}."))
        else:
            axis_ids = []
            for axis_id in axes:
                if axis_id.isdigit():
                    if 3>(axis_id:=int(axis_id))>=0:
                        if axis_id not in axis_ids:
                            axis_ids.append(axis_id)
                        else:
                            messages.append(Result(value=None , state=State.ERROR , message=f"Axis {axis_id} entered multiple times. Skipping duplicates."))
                    else:
                        messages.append(Result(value=None , state=State.ERROR , message=f"Axis {axis_id} is not a valid axis_id."))
                else:
                    messages.append(Result(value=None , state=State.ERROR , message=f"Axis {axis_id} is not a valid axis_id."))
            if axis_ids:
                try:
                    self.printer.home_Axes(axis_ids)
                    self.printer.save_State()
                    messages.append(Result(value=None , state=State.SUCCESS , message=f"Axes {axis_ids} homed successfully."))
                except Exception as e:
                    self.printer.save_State()
                    messages.append(Result(value="not all error" , state=State.ERROR , message=f"Error homing axes {axis_ids}. Error was: {e}."))
            else:
                messages.append(Result(value=None , state=State.ERROR , message="No valid axes input."))
        return messages

    def move(self , axis_id , method , amount=None):
        if not self.hardware_good:
            return Result(state = State.ERROR , message=f"Hardware is not good.")
        if not 0 <= axis_id < 3:
            return Result(state=State.ERROR , message=f"Error moving axis {axis_id}. Axis out of range.")
        if method == "top":
            try:
                self.printer.move_Axis_To_Top(axis_id)
                self.printer.save_State()
                return Result(state=State.SUCCESS , message=f"Successfully moved {axis_id} to top.")
            except Exception as e:
                return Result(state=State.ERROR , message=f"Error moving axis {axis_id} to top. Error was {e}")
        elif method == "absolute":
            try:
                self.printer.move_Axis_Absolute(axis_id , amount)
                self.printer.save_State()
                return Result(state=State.SUCCESS , message=f"Successfully moved {axis_id} to {amount} absolutely.")
            except Exception as e:
                return Result(state=State.ERROR , message=f"Error moving axis {axis_id} to {amount} absolutely. Error was {e}")
        elif method == "relative":
            try:
                self.printer.move_Axis_Relative(axis_id , amount)
                self.printer.save_State()
                return Result(state=State.SUCCESS , message=f"Successfully moved {axis_id} by {amount} relatively.")
            except Exception as e:
                return Result(state=State.ERROR , message=f"Error moving axis {axis_id} by {amount} relatively. Error was {e}")
        else:
            return Result(state=State.ERROR , message=f"Error moving with method {method}. Unknown method.")

    def get_Positions(self):
        try:
            pos = []
            for axis_id in range(3):
                pos.append(self.printer.get_Axis_Position(axis_id))
            return Result(value = pos , state = State.SUCCESS , message = "Successfully got positions")
        except Exception as e:
            return Result(state = State.ERROR , message = f"Error getting positions. Error was {e}.")

    def get_Temps(self):
        try:
            temps = {}
            temps["Chamber"] = self.printer.get_Temp(0)
            temps["Recoater Heater"] = self.printer.get_Temp(1)
            temps["Recoater Front"] = self.printer.get_Temp(2)
            return Result(value = temps , state = State.SUCCESS , message = f"Successfully got temps.")
        except Exception as e:
            return Result(state = State.ERROR , message = f"Error getting temp. Error was {e}")

    def get_Files(self):
        from lmm_printer.core.files import return_RM_Drives , get_Files
        drives_result = return_RM_Drives()
        if drives_result.state == State.ERROR:
            return drives_result
        drives = drives_result.value
        file_names , file_mnts = get_Files(drives)
        return Result(value = (file_names , file_mnts) , state = State.SUCCESS)

    def print(self):
        """
        Checks whether everything is read to print and prints if so.
        """
        self.stop_print = False

        from time import monotonic
        from lmm_printer.core.types import Print_File
        from lmm_printer.utils.vendored_handling import silence

        if not self.hardware_good:
            self.notify("Cannot start a print with bad hardware or connection. ")
            return
        if not self.file_good:
            self.notify("You must load a file before printing. ")
            return
        
        self.ui.start_Poll_During_Print()
        self.printer.start_Heaters()
        try:
            for i in range(1 , self.num_layers + 1):
                while not self.stop_print:
                    self.ui.poll_During_Print(self)
                    if self.printer.check_Heaters():
                        break
                self.ui.poll_During_Print(self)
                if self.stop_print:
                    self.stop_print = False
                    return
                with Print_File(self.file) as print_file:
                    if i == self.num_layers:
                        next_image = None
                    else:
                        next_image = print_file.get_Image(i + 1).value
                        
                    if i == 1:
                        this_image = print_file.get_Image(i).value
                        self.printer.init_Print(this_image , self.options)
                        # with silence():
                        #     self.printer.projector.send_pixeldata_to_buffer(this_image , 0 , 0)

                start_time = monotonic()
                self.printer.do_Current_Layer(next_image , self.options)
                end_time = monotonic()
                self.notify("Layer " + str(i) + " of " + str(self.num_layers) + " done. Took: " + str(end_time - start_time) + " seconds.")
        except Exception as e:
            self.stop_Print()
            self.notify(f"Error during print. Error was: {e}")

        
    def go(self):
        """
        Starts accepting commands and proceeds until the should_go flag is set to False.
        """

        self.load_Hardware()
        self.ui.start()
        while self.should_go:
            try:
                self.ui.get_Do_Command(self)
            except Exception as e:
                self.notify(Result(state=State.ERROR , message=f"Command failed with error {e}."))

    def quit(self):
        if self.hardware_good:
            self.printer.safe_Shutdown()
            self.should_go = False
        else:
            self.should_go = False

    def stop_Print(self):
        self.notify("Shutting down.")
        self.printer.stop_Active()
        self.printer.save_State()
        self.stop_print = True
from lmm_printer.core.types import Result , Move_Method , NUM_AXES , AXIS_NAMES , Session_Status

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
        self.should_go = True

        self.printer = None
        self.file = None
        self.num_layers = None
        self.printing = False
        self.current_layer = None

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
        if teensy_result.bad:
            teensy_loaded = False
        else:
            teensy_loaded = True
        teensy = teensy_result.value

        projector_result = return_Projector(self.config["projector"]["spi_max_speed"])
        self.notify(projector_result)
        if projector_result.bad:
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
        if image_result.bad:
            self.notify(image_result)
            print_file_error = True
        if options_result.bad:
            self.notify(options_result)
            print_file_error = True
        if print_file_error:
            return

        self.num_layers = num_layers
        self.options = options_result.value

    def home(self , axis_ids = None):
        if not axis_ids:
            axis_ids = list(range(NUM_AXES))
        axis_ids = list(set(axis_ids))
        axis_ids = [a for a in axis_ids if 0 <= a < NUM_AXES]

        if axis_ids:
            def action():
                self.printer.home_Axes(axis_ids)
                self.printer.save_State()
            description = f"Home axes: {[AXIS_NAMES(axis_id) for axis_id in axis_ids]}."
            return self._hardware_Action(description , action)
        else:
            return Result.error(message="No valid axes input.")

    def move(self , axis_id , method , amount=None):
        if not 0 <= axis_id < NUM_AXES:
            return Result.error(message=f"Error moving axis {axis_id}. Axis out of range.")

        def action():
            if method == Move_Method.TOP:
                self.printer.move_Axis_To_Top(axis_id)
            elif method == Move_Method.ABSOLUTE:
                self.printer.move_Axis_Absolute(axis_id , amount)
            elif method == Move_Method.RELATIVE:
                self.printer.move_Axis_Relative(axis_id , amount)
            self.printer.save_State()

        if method == Move_Method.TOP:
            description = f"Move {AXIS_NAMES(axis_id)} to top."
        elif method == Move_Method.ABSOLUTE:
            description = f"Move {AXIS_NAMES(axis_id)} to {amount} (absolute)."
        elif method == Move_Method.RELATIVE:
            description = f"Move {AXIS_NAMES(axis_id)} by {amount} (relative)."
        
        return self._hardware_Action(description , action)

    def get_Positions(self):
        def action():
            pos = []
            for axis_id in range(NUM_AXES):
                pos.append(self.printer.get_Axis_Position(axis_id))
            return pos
        description = f"Getting positions."
        return self._hardware_Action(description , action)

    def get_Temps(self):
        def action():
            temps = {}
            temps["Chamber"] = self.printer.get_Temp(0)
            temps["Recoater Heater"] = self.printer.get_Temp(1)
            temps["Recoater Front"] = self.printer.get_Temp(2)
            return temps
        description = f"Getting temps."
        return self._hardware_Action(description , action)
    
    def _hardware_Action(self , description , action):
        if self.printer is None:
            return Result.error("Printer hardware not connected.")
        try:
            value = action()
        except Exception as e:
            return Result.error(f"{description}: failed. Error was: {e}.")
        return Result.success(message=f"{description}: done." , value=value)

    def get_Files(self):
        from lmm_printer.core.files import return_RM_Drives , get_Files
        drives_result = return_RM_Drives()
        if drives_result.bad:
            return drives_result
        drives = drives_result.value
        files = get_Files(drives)
        return Result.success(value = files)

    def print(self):
        """
        Checks whether everything is read to print and prints if so.
        """
        self.stop_print = False

        from time import monotonic
        from lmm_printer.core.types import Print_File
        from lmm_printer.utils.vendored_handling import silence

        if self.printer is None: return Result.error("Cannot start a print with bad hardware or connection. ")
        if self.file is None: return Result.error("You must load a file before printing. ")

        self.stop_print = False
        self.printing = True
        
        self.ui.start_Poll_During_Print()

        try:
            self.printer.start_Heaters()
            for i in range(1 , self.num_layers + 1):
                self.current_layer = i
                while not self.stop_print:
                    self.ui.poll_During_Print(self)
                    if self.printer.check_Heaters():
                        break
                if self.stop_print: return Result.success("Print stopped.")

                with Print_File(self.file) as print_file:
                    if i == self.num_layers: next_image = None
                    else: next_image = print_file.get_Image(i + 1).value 
                    if i == 1:
                        first_image = print_file.get_Image(i).value
                        self.printer.init_Print(first_image , self.options)

                start_time = monotonic()
                self.printer.do_Current_Layer(next_image , self.options)
                end_time = monotonic()
                self.notify("Layer " + str(i) + " of " + str(self.num_layers) + " done. Took: " + str(end_time - start_time) + " seconds.")
            return Result.success("Print complete.")
        except Exception as e:
            return Result.error(f"Print failed on layer {self.current_layer}. Error was: {e}.")
        finally:
            self.printing = False
            self._make_safe

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
                self.notify(Result.error(message=f"Command failed with error {e}."))

    def quit(self):
        if self.printer is not None:
            self.printer.safe_Shutdown()
            self.should_go = False
        else:
            self.should_go = False

    def request_Stop(self):
        self.stop_print = True

    def _make_safe(self):
        try:
            self.printer.stop_Active()
        except Exception as e:
            self.notify(Result.error(f"Could not confirm heaters are off. Error was: {e}."))
        try:
            self.printer.save_State()
        except Exception as e:
            pass

    def get_Status(self):
        session_status = Session_Status()
        if self.printer is not None:
            session_status.hardware_connected = True
        if self.file is not None:
            session_status.file_name = self.file.name
            session_status.num_layers = self.num_layers
        if self.printing:
            session_status.printing = self.printing
            session_status.current_layer = self.current_layer
        return session_status
        
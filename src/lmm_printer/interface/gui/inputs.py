import sys , select
from lmm_printer.core.types import Result , State
from lmm_printer.interface.inputs import Generic_Input_Handler  , Generic_Print_Input_Handler

class Input_Handler(Generic_Input_Handler):
    """
    This is the main GUI input handler.
    """

    def suggestion(self):
        """
        Prints a helpful suggestion.
        """

        print("")
        print("Enter 'help' for a list of commands. ")

    def ask_Yes_No(self , message):
        """
        Asks a yes no question to the user.

        Parameters:
            message (str): The question to be asked.

        Returns:
            bool: True if the answer was yes, False if the answer was no. 
        """

        print("")
        print(message)
        print("'y' for yes, 'n' for no. ")
        while True:
            response = input("").strip().lower()
            if response == "y":
                return True
            elif response == "n":
                return False
            else:
                print("Enter 'y' or 'n'. ")

    def wait_To_Continue(self , message):
        """
        Prints a message and waits until the user pressed Enter to continue.

        Parameters:
            message (str): The message to be printed.
        """

        print("")
        print(message)
        print("Press Enter to continue. ")
        while True:
            response = input("").strip().lower()
            if response == "":
                return
            else:
                print("Invalid entry. ")

    def get_Do_Command(self , print_session):
        """
        Queries the user for a command and then does it.

        Parameters:
            print_session (Print_Session): The print session to act upon.
        """

        print("")
        response = input("Enter Command: ").strip().lower()

        if response == "help":
            self._help()
        elif response == "choose file":
            self._choose_File(print_session)
        elif response == "quit":
            self._quit(print_session)
        elif response == "home":
            self._home(print_session)
        elif response == "move":
            self._move(print_session)
        elif response == "get pos":
            self._get_Pos(print_session)
        elif response == "print":
            print_session.print()

    def _help(self):
        """
        Prints all of the commands.
        """

        print("")
        print("help: Prints this message. ")
        print("choose file: Enter the file select menu. ")
        print("quit: Quits the program safely. ")
        print("home: Enter the home menu. ")
        print("move: Enter the move menu. ")
        print("get pos: Gets the position of an axis. ")
        print("print: Prints selected file. ")

    def _choose_File(self , print_session):
        """
        Prints detected files and has the user choose one. 
        It then sends it to the print_session and has the print session load its attributes.

        Parameters:
            print_session (Print_Session): The print session to load the chosen file into.
        """

        from lmm_printer.core.files import return_RM_Drives , get_Files
        from pathlib import Path

        print("")
        drives_result = return_RM_Drives()
        print_session.output_handler.handle(drives_result)
        if drives_result.state == State.ERROR:
            return
        drives = drives_result.value

        file_names , file_mnts = get_Files(drives)
        print("Available Files: ")
        print(file_names)

        print("")
        response = input("Choose file by entering name.extension or press enter to return to command selection. ")

        if response.strip() == "":
            return
        else:
            response = response.strip()
            if response in file_names:
                index = file_names.index(response)
                mnt = file_mnts[index]
                file_result = Result(value = Path(mnt) / response , state = State.SUCCESS , message = "Successfully chose file: " + response + ", at mount: " + mnt + ".")
            else:
                print("File name invalid.")
                return self._choose_File(print_session)
        
        print_session.output_handler.handle(file_result)
        print_session.file = file_result.value
        print_session.load_Print_File_Attributes()

    def _quit(self , print_session):
        """
        Safely shuts down the printer and stops print_session.go() by setting the should_go flag to False.

        Parameters:
            print_session (Print_Session): The current print session.
        """

        if print_session.hardware_good:
            print_session.printer.safe_Shutdown()
            print_session.should_go = False
        else:
            print_session.should_go = False

    def _home(self , print_session):
        """
        Opens the home menu and queries the user for axes to move and the various movement modes.

        Parameters:
            print_session (Print_Session): The print session to act upon.
        """

        print("")
        print("Enter 'all' to home all axes. Enter axis number to home that axis. Press enter when finished.")
        print("Enter the axes you want to home one at a time and wait till they are done to continue. Enter 'all' to home all. Press enter once finished. ")
        while True:
            response = input("").strip()
            if response == "":
                break
            elif response == "all":
                print_session.printer.home_Axes() 
                print_session.printer.save_State()
                break
            try:
                axis_id = int(response)
                if (axis_id < 0) or (axis_id >= 3):
                    print_session.output_handler.handle("Axis ID: " + str(axis_id) + " invalid.")
                    continue
                print_session.printer.home_Axis(axis_id)
                print_session.printer.save_State()
            except Exception as e:
                print("Error homing axis " + response + ". Error is: " + str(e))

    def _relative(self , print_session , axis_id):
        """
        Queries the user for how many mm to move relative to the current position for a given axis.

        Parameters:
            print_session (Print_Session): The print session to act upon.
            axis_id (int): The axis number to move.
        """

        print("")
        print("Enter the amount of mm you want the axis to move up or down. Press Enter to return. ")
        while True:
            response = input("").strip()
            if response == "":
                break
            try:
                move = float(response)
                print_session.printer.move_Axis_Relative(axis_id , move)
                print_session.printer.save_State()
            except Exception as e:
                print_session.output_handler.handle("Error moving " + response + " mm. Error is: " + str(e))

    def _absolute(self , print_session , axis_id):
        """
        Queries the user for what position a given axis should move.

        Parameters:
            print_session (Print_Session): The print session to act upon.
            axis_id (int): The axis number to move.
        """

        print("")
        print("Enter the position you want the axis to move to. Press Enter to return. ")
        while True:
            response = input("").strip()
            if response == "":
                break
            try:
                move = float(response)
                print_session.printer.move_Axis_Absolute(axis_id , move)
                print_session.printer.save_State()
            except Exception as e:
                print("Error moving " + response + " mm. Error is: " + str(e))

    def _move(self , print_session):
        """
        Queries the user on which axis to move, then prints the possible move types and queries for those.
        Stays active, allowing for multiple inputs until the user enters.

        Parameters:
            print_session (Print_Session): The print session to act upon.
        """

        while True:
            print("")
            print("Enter the axis to move. Press Enter to return")
            response = input("").strip().lower()
            if response == "":
                break
            try:
                axis_id = int(response)
                if (axis_id < 0) or (axis_id >= 3):
                    print_session.output_handler.handle("Axis ID: " + str(axis_id) + " out of bounds.")
                    continue
                print("")
                print("top: Move axis to its maximum. ")
                print("relative: Move axis relative to current position in mm. ")
                print("absolute: Move axis relative to current position in mm. ")
                response = input("").strip().lower()
                if response == "top":
                    print_session.printer.move_Axis_To_Top(axis_id)
                    print_session.printer.save_State()
                elif response == "relative":
                    self._relative(print_session , axis_id)
                elif response == "absolute":
                    self._absolute(print_session , axis_id)
                else:
                    print("Invalid command. ")
            except Exception as e:
                print_session.output_handler.handle("Error moving axis. Error was: " + str(e))

    def _get_Pos(self , print_session):
        """
        Queries the user for which axis' position to output using the output handler
        in the passed print_session.

        Parameters:
            print_session (Print_Session): The print session to act upon.
        """

        # print("")
        # print("Enter the axis number to see its position. Press enter when finished.")
        # while True:
        #     response = input("").strip()
        #     if response == "":
        #         break
        #     try:
        #         axis_id = int(response)
        #         if (axis_id < 0) or (axis_id >= 3):
        #             print_session.output_handler.handle("Axis ID: " + str(axis_id) + " invalid.")
        #             continue
        #         pos = print_session.printer.get_Axis_Position(axis_id)
        #         print_session.output_handler.handle("Position of axis " + str(axis_id) + " is " + str(pos))
        #     except Exception as e:
        #         print("Error checking position of axis " + response + ". Error is: " + str(e))

        for axis_id in range(3):
            pos = print_session.printer.get_Axis_Position(axis_id)
            print_session.output_handler.handle("Position of axis " + str(axis_id) + " is " + str(pos))

class Print_Input_Handler(Generic_Print_Input_Handler):
    """
    This is the asynchronous CLI input handler for use during a print.
    """
    
    def suggestion(self):
        """
        Prints a helpful suggestion.
        """
        print("Enter h at any time for a list of commands. ")

    def handle(self , print_session):
        """
        Handles the buffer of inputs.

        Parameters:
            print_session (Print_Session): The print session to act upon.
        """

        while self._line_Ready():
            cmd = sys.stdin.readline().strip().lower()
            self._dispatch(cmd , print_session)

    def _dispatch(self , inp , print_session):
        """
        Dispatches a command.

        Parameters: 
        inp (str): The input command as a string.
        print_session (Print_Session): The print session to act upon.
        """

        if inp == "h":
            print("")
            print("h: Prints this message.")
            print("p: Pauses the printer.")
            print("q: Safely quits the process.")
            print("t: Show the temperatures of probes. ")
            print("Note - neither pausing nor quitting will stop axes from completing their current move.")
            print("")

        elif inp == "p":
            print("Enter r to resume.")
            while True:
                response = input("").strip().lower()
                if response == "r":
                    break
                    
        elif inp == "q":
            from lmm_printer.utils.vendored_handling import silence
            print("Shutting down.")
            print_session.printer.save_State()
            with silence():
                print_session.printer.projector.stop_exposure()
            print_session.printer.set_Heater(0 , 0)
            print_session.printer.set_Heater(1 , 0)
            print_session.stop_print = True

        elif inp == "t":
            print("Chamber: " + str(print_session.printer.get_Temp(0)))
            print("Recoater Heater: " + str(print_session.printer.get_Temp(1)))
            print("Recoater Front: " + str(print_session.printer.get_Temp(2)))
            
    def _line_Ready(self):
        """
        Checks whether there is an input waiting.
        """

        return select.select([sys.stdin] , [] , [] , 0)[0] != []
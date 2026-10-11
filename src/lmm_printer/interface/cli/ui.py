import sys , select
from lmm_printer.interface.ui import Generic_UI
from lmm_printer.core.types import Result , State

class UI(Generic_UI):
    def start(self):
        """
        Prints a helpful suggestion.
        """

        print("")
        print("Enter 'help' for a list of commands. ")

    def notify(self , message):
        """
        Takes a message and hands it off to a handler function

        Parameters:
            message: The message to be output.
        """

        if isinstance(message , str):
            self._notify_String(message)
        elif isinstance(message , Result):
            self._notify_Result(message)
        else:
            self._notify_Unknown_Type(message)

    def _notify_String(self , message):
        """
        Prints a string message.

        Parameters:
            message (str): Message to be printed.
        """

        print("")
        print(message)

    def _notify_Result(self , message):
        """
        Prints the message associated with the Result type.

        Parameters:
            message (Result): The message result to be printed.
        """

        print("")
        print(message.message)

    def _notify_Unknown_Type(self , message):
        """
        Handles unknown message types by printing an error message which contains the message.

        Parameters:
            message: The message to be printed.
        """

        print("")
        error_message = "Message: " + str(message) + " has unknown output type. "
        print(error_message)

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

    def wait_To_Continue(self, message):
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
        response = input("Enter Command: ").strip().lower().split()
        command = response[0] if len(response) else None
        args = response[1:] if len(response)>1 else None

        if command == "help":
            self._help()
        elif command == "chooseFile":
            self._choose_File(print_session)
        elif command == "printFiles":
            self._print_Files(print_session)
        elif command == "quit":
            self._quit(print_session)
        elif command == "home":
            self._home(print_session , args)
        elif command == "move":
            self._move(print_session , args)
        elif command == "getPos":
            self._get_Pos(print_session , args)
        elif command == "print":
            self.start_Poll_During_Print()
            print_session.print()

    def _help(self):
        """
        Prints all of the commands.
        """

        print("")
        print("help: Prints this message. ")
        print("chooseFile: Loads name.extension. Traces -> \n\t chooseFile <name.extension>")
        print("printFiles: Prints all found files. ")
        print("quit: Quits the program safely. ")
        print("home: Homes all or the given axes. Traces -> \n\t home all \n\t home <axis_a> <axis_b> <axis_c>  ")
        print("move: Moves an axis with a given method by some amount. Traces -> \n\t move <axis_id> relative <amount> \n\t move <axis_id> absolute <position> \n\t move <axis_id> top")
        print("getPos: Gets the position of all axes. ")
        print("print: Prints selected file. ")

    def _get_Files(self):
        from lmm_printer.core.files import return_RM_Drives , get_Files
        drives_result = return_RM_Drives()
        if drives_result.state == State.ERROR:
            return drives_result
        drives = drives_result.value
        file_names , file_mnts = get_Files(drives)
        return Result(value = (file_names , file_mnts) , state = State.SUCCESS)

    def _print_Files(self):
        files_result = self._get_Files()
        if files_result.state == State.ERROR:
            self.notify(files_result)
            return
        file_names , _ = files_result.value
        if file_names:
            print("")
            print("Available Files")
            for file_name in file_names:
                print(file_name)

    def _choose_File(self , print_session , args):
        """
        Prints detected files and has the user choose one. 
        It then sends it to the print_session and has the print session load its attributes.

        Parameters:
            print_session (Print_Session): The print session to load the chosen file into.
        """

        from pathlib import Path

        files_result = self._get_Files()
        if files_result.state == State.ERROR:
            self.notify(files_result)
            return
        file_names , file_mnts = files_result.value

        file_name = args[0]
        if file_name in file_names:
            index = file_names.index(file_name)
            mnt = file_mnts[index]
            file_result = Result(value = Path(mnt) / file_name , state = State.SUCCESS , message = "Successfully chose file: " + file_name + ", at mount: " + mnt + ".")
            self.notify(file_result)
            print_session.load_Print_File(file_result.value)
        else:
            print("File name not found. Did you include the extension?")


    def _quit(self , print_session):
        """
        Safely shuts down the printer and stops print_session.go() by setting the should_go flag to False.

        Parameters:
            print_session (Print_Session): The current print session.
        """

        print_session.quit()

    def _home(self , print_session , args):
        """
        Opens the home menu and queries the user for axes to move and the various movement modes.

        Parameters:
            print_session (Print_Session): The print session to act upon.
        """

        if args:
            results = print_session.home(args)
        else:
            print("")
            print("Enter 'all' to home all axes. Enter a space separated list of axis ids to home those axes. Press enter when finished.")
            responses = input("").strip().split()
            results = print_session.home(responses)

        for result in results:
            self.notify(result)

    def _move(self , print_session , args):
        """
        Queries the user on which axis to move, then prints the possible move types and queries for those.
        Stays active, allowing for multiple inputs until the user enters.

        Parameters:
            print_session (Print_Session): The print session to act upon.
        """

        if args[-1] == "top":
            if len(args)>1:
                if args[0].isdigit():
                    axis_id = int(args[0])
                else:
                    print("Provide a valid axis id.")
                    return
            else:
                print("Provide an axis to move to top.")
                return
            result = print_session.move(axis_id , method="top")

        elif len(args)>2 and args[1]=="absolute":
            if args[0].isdigit():
                axis_id = int(args[0])
            else:
                print("Provide a valid axis id.")
                return
            
            try:
                amount = float(args[2])
            except ValueError:
                print("Enter a valid position to move to.")
                return

            result = print_session.move(axis_id , method="absolute" , amount=amount)

        elif args[1] == "relative":
            if args[0].isdigit():
                axis_id = int(args[0])
            else:
                print("Provide a valid axis id.")
                return
            
            try:
                amount = float(args[2])
            except ValueError:
                print("Enter a valid amount to move by.")
                return

            result = print_session.move(axis_id , method="relative" , amount=amount)

        else:
            if args[0].isdigit():
                axis_id = int(args[0])
            else:
                print("Provide a valid axis id.")
                return
            
            try:
                amount = float(args[1])
            except ValueError:
                print("Enter a valid amount to move by.")
                return

            result = print_session.move(axis_id , method="relative" , amount=amount)

        self.notify(result)


    def _get_Pos(self , print_session):
        """
        Prints the postions of all axes

        Parameters:
            print_session (Print_Session): The print session to act upon.
        """

        for axis_id in range(3):
            pos = print_session.printer.get_Axis_Position(axis_id)
            self.notify("Position of axis " + str(axis_id) + " is " + str(pos))

    def start_Poll_During_Print(self):
        """
        Prints a helpful suggestion.
        """
        print("Enter h at any time for a list of commands. ")

    def poll_During_Print(self , print_session):
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


import sys , select
from lmm_printer.interface.ui import Generic_UI
from lmm_printer.core.types import Result , Move_Method , AXIS_NAMES

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
        response = input("Enter Command: ").strip().split()
        command = response[0].lower() if len(response) else None
        args = response[1:] if len(response)>1 else None

        if command == "help":
            self._help()
        elif command == "choosefile":
            self._choose_File(print_session , args)
        elif command == "printfiles":
            self._print_Files(print_session)
        elif command == "quit":
            self._quit(print_session)
        elif command == "home":
            self._home(print_session , args)
        elif command == "move":
            self._move(print_session , args)
        elif command == "getpos":
            self._get_Pos(print_session)
        elif command == "print":
            self.notify(print_session.print())
        elif command is None:
            return
        else:
            print("Unknown command. Enter 'help' for help.")

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
        print("getpos: Gets the position of all axes. ")
        print("print: Prints selected file. ")

    def _print_Files(self , print_session):
        files_result = print_session.get_Files()
        if files_result.bad:
            self.notify(files_result)
            return
        files = files_result.value
        if files:
            print("")
            print("Available Files:")
            for file in files:
                print(file.name)
        else:
            print("")
            print("No Files Found.")

    def _choose_File(self , print_session , args):
        """
        Prints detected files and has the user choose one. 
        It then sends it to the print_session and has the print session load its attributes.

        Parameters:
            print_session (Print_Session): The print session to load the chosen file into.
        """

        if not args:
            print("Enter a file to choose. ")
            return

        files_result = print_session.get_Files()
        if files_result.bad:
            self.notify(files_result)
            return
        files = files_result.value
        file_names = [file.name for file in files]

        file_name = args[0]
        if file_name in file_names:
            index = file_names.index(file_name)
            file_result = Result.success(value = files[index] , message = f"Successfully chose file: {file_name} with path {files[index]}.")
            self.notify(file_result)
            print_session.load_Print_File(file_result.value)
        else:
            self.notify("File name not found. Did you include the extension?")

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
        if not args:
            result = Result.error(message = "You must enter a some axes to home. Enter 'help' for help.")
        else:
            if 'all' in args:
                result = print_session.home()
            else:
                args = [int(arg) for arg in args if arg.isdigit()]
                if not args:
                    result = Result.error(message = "No valid arguments entered.")
                else:
                    result = print_session.home(args)

        self.notify(result)

    def _move(self , print_session , args):
        """
        Queries the user on which axis to move, then prints the possible move types and queries for those.
        Stays active, allowing for multiple inputs until the user enters.

        Parameters:
            print_session (Print_Session): The print session to act upon.
        """
        trace_error = "Use a correct trace. Enter 'help' for a list of commands with their traces."
        if not args or len(args)<2:
            print(trace_error); return
        axis_id , method , amount = args[0] , args[1].lower() , None

        if not axis_id.isdigit():
            if axis_id in AXIS_NAMES:
                axis_id = AXIS_NAMES.index(axis_id)
            else:
                self.notify(f"Axis id is not an integer or one of the following {AXIS_NAMES}.")
                return
        else:
            axis_id = int(axis_id)

        if method == "relative":
            method = Move_Method.RELATIVE
        elif method == "absolute":
            method = Move_Method.ABSOLUTE
        elif method == "top":
            method = Move_Method.TOP

        if method in (Move_Method.RELATIVE , Move_Method.ABSOLUTE):
            if len(args)<3: print(trace_error); return
            try: amount = float(args[2])
            except ValueError: print(trace_error); return
        elif method != Move_Method.TOP:
            try: amount = float(args[1]); method = Move_Method.RELATIVE
            except ValueError: print(trace_error); return

        self.notify(print_session.move(axis_id , method , amount))

    def _get_Pos(self , print_session):
        """
        Prints the postions of all axes

        Parameters:
            print_session (Print_Session): The print session to act upon.
        """

        result = print_session.get_Positions()
        if result.good:
            for axis_id , pos in enumerate(result.value):
                print(f"{AXIS_NAMES[axis_id]}: {pos} mm.")
        else:
            self.notify(result)


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
            print_session.request_Stop()

        elif inp == "t":
            result = print_session.get_Temps()
            if result.good:
                for key , value in result.value.items():
                    print(f"{key}: {value}")
            else:
                self.notify(result)
            
    def _line_Ready(self):
        """
        Checks whether there is an input waiting.
        """

        return select.select([sys.stdin] , [] , [] , 0)[0] != []


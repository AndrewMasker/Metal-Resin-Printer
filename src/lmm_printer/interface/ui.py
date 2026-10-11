from abc import ABC , abstractmethod

class Generic_UI(ABC):
    @abstractmethod
    def start(self):
        """
        This is a function that starts the ui.
        """
        ...

    @abstractmethod
    def notify(self , message):
        """
        Notifies the user with some message.
        """
        ...

    @abstractmethod
    def ask_Yes_No(self , message):
        """
        Asks the user a yes or no question.
        """
        ...

    @abstractmethod
    def wait_To_Continue(self , message):
        """
        Prints a message and waits for the user to continue.
        """
        ...

    @abstractmethod
    def get_Do_Command(self , print_session):
        """
        This is a blocking idle menu that waits until a command is recieved and does it.
        """
        ...

    @abstractmethod
    def poll_During_Print(self , print_session):
        """
        This is a handler that polls for commands during the print.
        """
        ...

    @abstractmethod
    def start_Poll_During_Print(self):
        """
        This is the function that starts the polling during print.
        """
        ...
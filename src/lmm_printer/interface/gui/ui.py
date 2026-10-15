from lmm_printer.interface.ui import Generic_UI
from lmm_printer.interface.gui.menu_items import Theme , Selected_Theme , Captured_Theme
from lmm_printer.interface.gui.menus import Menu_Handler , main_Menu
from lmm_printer.interface.gui.input import Encoder_Input
from lmm_printer.interface.gui.display import Framebuffer , find_Panel
import pygame

class UI(Generic_UI):
    def __init__(self , print_session , config):
        self.config = config
        self.width = self.config["display"]["width"]
        self.width = self.config["display"]["height"]

        pygame.display.init()
        pygame.font.init()

        self.canvas = pygame.display.set_mode((self.width , self.height))

        font = pygame.font.SysFont("Arial", 24)
        self.themes = (Theme(font=font) , Selected_Theme(font=font) , Captured_Theme(font=font))

        main_menu = main_Menu(print_session , self.notify)
        self.main_handler = Menu_Handler(main_menu , self.notify)

        self.input = Encoder_Input()

        panel_path = find_Panel()
        self.framebuffer = Framebuffer(panel_path , (self.width , self.height))


    def start(self):
        """
        This is a function that starts the ui.
        """
        return

    def notify(self , message):
        """
        Notifies the user with some message.
        """
        return

    def ask_Yes_No(self , message):
        """
        Asks the user a yes or no question.
        """
        return

    def wait_To_Continue(self , message):
        """
        Prints a message and waits for the user to continue.
        """
        return

    def get_Do_Command(self , print_session):
        """
        This is a blocking idle menu that waits until a command is recieved and does it.
        """
        turns , pressed = self.input.read()
        self.main_handler.do_Input(turns , pressed)
        return

    def poll_During_Print(self , print_session):
        """
        This is a handler that polls for commands during the print.
        """
        return

    def start_Poll_During_Print(self):
        """
        This is the function that starts the polling during print.
        """
        return
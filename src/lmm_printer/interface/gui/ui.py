from lmm_printer.interface.ui import Generic_UI
from lmm_printer.interface.gui.menu_items import Theme , Selected_Theme , Captured_Theme
from lmm_printer.interface.gui.menus import Menu_Handler , main_Menu
from lmm_printer.interface.gui.input import Encoder_Input
from lmm_printer.interface.gui.display import Framebuffer , find_Panel
import pygame

class UI(Generic_UI):
    def __init__(self , print_session , config):
        self.config = config

        pygame.display.init()
        pygame.font.init()

        self._set_canvases()

        font = pygame.font.SysFont("Arial", 24)
        self.themes = (Theme(font=font) , Selected_Theme(font=font) , Captured_Theme(font=font))

        main_menu = main_Menu(print_session , self.notify)
        self.main_handler = Menu_Handler(main_menu , self.notify)

        self.input = Encoder_Input()

        panel_path = find_Panel()
        self.framebuffer = Framebuffer(panel_path , (self.width , self.height))

    def _set_canvases(self):
        width = self.config["display"]["width"]
        height = self.config["display"]["height"]
        self.canvas = pygame.display.set_mode((width , height))

        menu_width = self.config["display"]["menu"]["width"]
        menu_height = self.config["display"]["menu"]["height"]
        menu_x = self.config["display"]["menu"]["x"]
        menu_y = self.config["display"]["menu"]["y"]
        menu_rect = pygame.Rect(menu_x , menu_y , menu_width , menu_height)
        self.menu_canvas = self.canvas.subsurface(menu_rect)

        notify_width = self.config["display"]["notify"]["width"]
        notify_height = self.config["display"]["notify"]["height"]
        notify_x = self.config["display"]["notify"]["x"]
        notify_y = self.config["display"]["notify"]["y"]
        notify_rect = pygame.Rect(notify_x , notify_y , notify_width , notify_height)
        self.notify_canvas = self.canvas.subsurface(notify_rect)

        status_width = self.config["display"]["status"]["width"]
        status_height = self.config["display"]["status"]["height"]
        status_x = self.config["display"]["status"]["x"]
        status_y = self.config["display"]["status"]["y"]
        status_rect = pygame.Rect(status_x , status_y , status_width , status_height)
        self.status_canvas = self.canvas.subsurface(status_rect)

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
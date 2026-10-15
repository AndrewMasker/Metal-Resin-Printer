from lmm_printer.interface.ui import Generic_UI
from lmm_printer.interface.gui.menu_items import Theme , Selected_Theme , Captured_Theme
from lmm_printer.interface.gui.menus import Menu_Handler , main_Menu , print_Menu
from lmm_printer.interface.gui.input import Encoder_Input
from lmm_printer.interface.gui.display import Framebuffer , find_Panel
from lmm_printer.interface.gui.text_output import Text_Output
from lmm_printer.core.types import Result
import threading , queue
import pygame

class UI(Generic_UI):
    def __init__(self , print_session , config):
        self.config = config
        self.menu_dirty , self.notify_dirty , self.status_dirty = True , True , True

        pygame.display.init()
        pygame.font.init()

        self._set_canvases()

        font = pygame.font.SysFont("Arial", 24)
        self.themes = (Theme(font=font) , Selected_Theme(font=font) , Captured_Theme(font=font))

        self.input = Encoder_Input()

        width = self.config["display"]["width"]
        height = self.config["display"]["height"]
        panel_path = find_Panel()
        self.framebuffer = Framebuffer(panel_path , (width , height))

        self.text_output = Text_Output(self.config["display"]["notify"]["max_lines"] , Theme(font=font))
        self._init_Poll_During_Print()
        self._set_Menu_Handlers(print_session)
        

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

    def _set_Menu_Handlers(self , print_session):
        main_menu = main_Menu(print_session , self.notify)
        self.main_handler = Menu_Handler(main_menu , self.notify)

        print_menu = print_Menu(print_session , self.notify , self.commands)
        self.print_handler = Menu_Handler(print_menu , self.notify)

    def start(self):
        """
        This is a function that starts the ui.
        """
        return

    def notify(self , message):
        """
        Notifies the user with some message.
        """
        if isinstance(message , Result):
            message = message.message
        elif isinstance(message , str):
            message = message
        else:
            message = f"{message}"

        self.text_output.push(message)
        self.notify_dirty = True

    def _draw_Notify(self):
        if self.notify_dirty:
            self.notify_dirty = False
            self.notify_canvas.fill(self.text_output.theme.body_color)
            self.text_output.draw(self.notify_canvas)
            self.framebuffer.show(self.canvas)

    def get_Do_Command(self , print_session):
        """
        This is a blocking idle menu that waits until a command is recieved and does it.
        """
        turns , pressed = self.input.read()
        if turns or pressed:
            self.main_handler.do_Input(turns , pressed)
            self.menu_dirty = True

        self._draw_Menu_Area(self.main_handler , self.menu_canvas)
        self._draw_Notify()

    def _draw_Menu_Area(self , handler , menu_canvas):
        if self.menu_dirty:
            self.menu_dirty = False
            menu_canvas.fill(self.themes[0].body_color)
            handler.draw(menu_canvas , self.themes)
            self.framebuffer.show(self.canvas)
            

    def poll_During_Print(self , print_session):
        """
        This is a handler that polls for commands during the print.
        """
        while self._run_Command(wait = .5):
            pass

    def _ui_Loop(self):
        while not self.stop_event.is_set():
            turns , pressed = self.input.read()
            if turns or pressed:
                self.print_handler.do_Input(turns , pressed)
                self.menu_dirty = True

            self._draw_Menu_Area(self.print_handler , self.menu_canvas)
            self._draw_Notify()

    def _run_Command(self , wait = None):
        try:
            action = self.commands.get(timeout=wait) if wait else self.commands.get_nowait()
        except queue.Empty:
            return False
        result = action()
        if isinstance(result , Result) and result.message:
            self.notify(result)
        return True

    def _init_Poll_During_Print(self):
        self.commands = queue.Queue()
        self.stop_event = threading.Event()

    def start_Poll_During_Print(self):
        """
        This is the function that starts the polling during print.
        """
        self.menu_dirty = True
        self.thread = threading.Thread(target = self._ui_Loop , daemon=True)
        self.thread.start()
        
        
    def stop_Poll_During_Print(self):
        self.stop_event.set()
        self.thread.join()
        self.stop_event.clear()
        while not self.commands.empty():
            _ = self.commands.get_nowait()
        while self.print_handler.pop():
            pass
        self.menu_dirty = True




    
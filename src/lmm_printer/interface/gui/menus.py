from lmm_printer.interface.gui import menu_items as m
from lmm_printer.core.types import Result
from dataclasses import dataclass
import pygame

@dataclass
class Menu_Frame:
    menu: list = None
    cursor: int = 0

class Menu_Handler():
    def __init__(self , init_menu , notify):
        self.menu_stack = [Menu_Frame(menu=init_menu)]
        self.notify = notify

    def push(self , menu):
        if not menu:
            self.notify(Result.error("Sub menu is empty."))
            return
        menu_frame = Menu_Frame(menu=menu)
        self.menu_stack.append(menu_frame)
        result = self._make_Cursor_Valid()
        if result.bad:
            self.notify(result)
            self.pop()

    def pop(self , index = -1):
        if len(self.menu_stack)>1:
            self.menu_stack.pop(index)

    def get_Current(self):
        menu = self.menu_stack[-1].menu
        cursor = self.menu_stack[-1].cursor
        item = menu[cursor] if cursor < len(menu) else None
        return menu , cursor , item

    def set_Cursor(self , cursor):
        self.menu_stack[-1].cursor = cursor
        
    def do_Input(self , turns , pressed):
        result = self._make_Cursor_Valid()
        if result.bad:
            self.notify(result)
            return
        
        _ , _ , item = self.get_Current()

        if pressed:
            result = item.on_Press(self)
            if result is not None and result.bad:
                self.notify(result)
        elif turns:
            result = item.on_Turn(turns)
            if result is not None and result.bad:
                self.notify(result)
            if not item.captured:
                self._navigate(turns)

    def _navigate(self , turns):
        _ , cursor , _ = self.get_Current()
        cursor = cursor + turns
        self.set_Cursor(cursor=cursor)
        self._make_Cursor_Valid(down = turns>0)

    def _make_Cursor_Valid(self , down = True):
        menu , cursor , _ = self.get_Current()

        num_items = len(menu)

        def put_In_Menu(cursor):
            if cursor >= num_items:
                cursor = 0
            if cursor < 0:
                cursor = num_items - 1
            return cursor

        cursor = put_In_Menu(cursor)
        increment = 1 if down == True else -1

        for _ in range(num_items):
            if menu[cursor].cursor:
                break
            else:
                cursor += increment
                cursor = put_In_Menu(cursor)
        else:
            return Result.error(message="The menu at the end of the stack has no valid cursor locations.")

        self.menu_stack[-1] = Menu_Frame(menu=menu , cursor=cursor)
        return Result.success()

    def draw(self , canvas , themes):
        canvas_width , canvas_height = canvas.get_size()
        menu , cursor , item = self.get_Current()
        menu_height = 0
        cursor_depth = 0
        for index , item in enumerate(menu):
            menu_height += themes[item.editing + (index == cursor)].height
            cursor_depth += themes[item.editing + (index == cursor)].height if index<cursor else 0
        canvas_midpoint = canvas_height//2
        if cursor_depth < canvas_midpoint:
            offset = 0
        elif canvas_midpoint <= cursor_depth <= (menu_height - canvas_midpoint):
            offset = canvas_midpoint - cursor_depth
        else:
            offset = canvas_height - menu_height

        item_depth = 0
        for index , item in enumerate(menu):
            theme = themes[item.editing + selected]
            item_height = theme.height
            selected = index == cursor
            item_depth += item_height
            item_offset = item_depth + offset
            rect = pygame.Rect(0 , item_offset , canvas_width , item_height)
            item.draw(canvas.subsurface(rect) , selected , themes)
        
        

def main_Menu(print_session):

    title = m.Title("Main Menu")
    num_select = m.Num_Select("Select Number: " , step = .5)
    print_item = m.Leaf("Print")

    print_item.action = lambda: print(num_select.value)

    return [title , num_select , print_item]
    
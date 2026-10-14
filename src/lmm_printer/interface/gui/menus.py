from lmm_printer.interface.gui import menu_items as m
from lmm_printer.core.types import Result , NUM_AXES , AXIS_NAMES , Move_Method
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
            menu_height += themes[item.captured + (index == cursor)].height
            cursor_depth += themes[item.captured + (index == cursor)].height if index<cursor else 0
        canvas_midpoint = canvas_height//2
        if menu_height>canvas_height:
            if cursor_depth < canvas_midpoint:
                offset = 0
            elif canvas_midpoint <= cursor_depth <= (menu_height - canvas_midpoint):
                offset = canvas_midpoint - cursor_depth
            else:
                offset = canvas_height - menu_height
        else:
            offset = 0

        item_depth = 0
        for index , item in enumerate(menu):
            selected = index == cursor
            theme = themes[item.captured + selected]
            item_height = theme.height
            item_offset = item_depth + offset
            rect = pygame.Rect(0 , item_offset , canvas_width , item_height)
            item_depth += item_height
            if not canvas.get_rect().contains(rect): continue
            item.draw(canvas.subsurface(rect) , selected , themes)
            
        
def main_Menu(print_session , menu_handler):

    title = m.Title("LMM Printer")
    move = m.Branch("Move" , sub_menu=_move_Menu(print_session))
    home = m.Branch("Home" , sub_menu=_home_Menu(print_session))
    choose_file = m.Branch("Choose File" , sub_menu=_choose_File_Menu(print_session))
    print_item = m.Leaf("Begin Print" , action=print_session.print())
    quit_item = m.Leaf("Quit" , action=print_session.quit())

    return [title , move , home , choose_file , print_item , quit_item]

def _move_Menu(print_session , menu_handler):
    menu = []
    menu.append(m.Title("Choose Axis to Move"))
    for i in range(NUM_AXES):
        menu.append(m.Branch(label=AXIS_NAMES[i].title() , sub_menu=lambda:_move_Method_Menu(print_session , menu_handler , i)))
    menu.append(m.Leaf(label="Back" , action = menu_handler.pop))
    return menu

def _move_Method_Menu(print_session , menu_handler , axis_id):
    title = m.Title(f"Choose method to move {AXIS_NAMES[axis_id]}")
    absolute = m.Branch(label="Absolute" , sub_menu=lambda: _move_Axis_Menu(print_session , menu_handler , axis_id , Move_Method.ABSOLUTE))
    relative = m.Branch(label="Absolute" , sub_menu=lambda: _move_Axis_Menu(print_session , menu_handler , axis_id , Move_Method.RELATIVE))
    top = m.Branch(label="Absolute" , sub_menu=lambda: _move_Axis_Menu(print_session , menu_handler , axis_id , Move_Method.TOP))
    back = m.Leaf(label="Back" , action = menu_handler.pop)
    return [title , absolute , relative , top , back]

def _move_Axis_Menu(print_session , menu_handler , axis_id , move_method):
    title = m.Title(f"Move {AXIS_NAMES[axis_id]} {move_method.value}.")
    go = m.Leaf(label="Go")
    back = m.Leaf(label="Back" , action = menu_handler.pop)

    if move_method is not Move_Method.TOP:
        num_select = m.Num_Select(label="Choose Amount:" , value=0 , step=.5)
        go.action = lambda: print_session.move(axis_id , move_method , num_select.value)
        return [title , num_select , go , back]
    else:
        go.action = lambda: print_session.move(axis_id , move_method)
        return [title , go , back]

def _home_Menu(print_session , menu_handler):
    menu = []
    menu.append(m.Title("Choose Axes to Home"))
    for i in range(NUM_AXES):
        menu.append(m.Checkbox(label=AXIS_NAMES[i].title()))
    menu.append(m.Leaf(label="Go" , action=lambda: print_session.home([i for i , item in enumerate(menu[1:]) if item.is_checked])))
    menu.append(m.Leaf(label="Back" , action = menu_handler.pop))
    return menu

def _choose_File_Menu(print_session , menu_handler):
    result = print_session.get_Files()
    if result.bad:
        menu_handler.notify(result)
        return
    files = result.value
    if not files:
        menu_handler.notify("No Files Found")
        return
    menu = []
    menu.append(m.Title("Choose File"))
    for file in files:
        menu.append(m.Leaf(label=file.name , action=lambda: (print_session.load_Print_File(file) , menu_handler.pop())[0]))
    menu.append(m.Leaf(label="Back" , action = menu_handler.pop))
    return menu

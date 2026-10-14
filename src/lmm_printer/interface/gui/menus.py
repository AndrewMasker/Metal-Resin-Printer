from lmm_printer.interface.gui import menu_items as m
from lmm_printer.core.types import Result
from dataclasses import dataclass

@dataclass
class Menu_Frame:
    menu: list = None
    cursor: int = 0

class Menu_Handler():
    def __init__(self , init_menu , notify , config):
        self.menu_stack = [Menu_Frame(menu=init_menu)]
        self.notify = notify
        self.config = config

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
            return result
        
        _ , _ , item = self.get_Current()

        if pressed:
            result = item.on_Press(self)
        elif turns:
            result = item.On_Turns(turns)
        if not item.captured:
            self._navigate()

    def _num_Select(self , turns , pressed):
        _ , _ , item = self.get_Current()
        if item.editing:
            if pressed:
                item.editing = False
                return
            item.value += turns * item.step
        else:
            if pressed: item.editing = True; return
            self._navigate(turns)

    def _leaf(self , turns , pressed):
        if pressed:
            _ , _ , item = self.get_Current()
            try: 
                item.action()
                return Result.success()
            except Exception as e:
                return Result.error(message=f"Error doing {item.label}. Error was: {e}.")
        else:
            self._navigate(turns)
            return Result.success()

    def _branch(self , turns , pressed):
        if pressed:
            _ , _ , item = self.get_Current()
            try:
                menu = item.submenu()
            except Exception as e:
                return Result.error(f"Error opening submenu. Error was: {e}.")
            menu_frame = Menu_Frame(menu=menu)
            self.menu_stack.append(menu_frame)
            return Result.success()
        else:
            self._navigate(turns)

    def _checkbox(self , turns , pressed):
        _ , _ , item = self.get_Current()
        if item.editing:
            if pressed:
                item.editing = False
                return
            if turns:
                item.is_checked = not item.is_checked
                return
        else:
            if pressed:
                item.editing = True
                return
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

    def draw(self):
        menu , cursor , item = self.get_Current()

def main_Menu(print_session):

    title = m.Title("Main Menu")
    num_select = m.Num_Select("Select Number: " , step = .5)
    print_item = m.Leaf("Print")

    print_item.action = lambda: print(num_select.value)

    return [title , num_select , print_item]
    
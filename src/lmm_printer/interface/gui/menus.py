import menu_items as m
from core.types import Result
from dataclasses import dataclass

@dataclass
class Menu_Frame:
    menu: list = None
    cursor: int = 0

class Menu_Handler():
    def __init__(self , init_menu):
        self.menu_stack = [init_menu]

    def get_Current(self):
        menu = self.menu_stack[-1].menu
        cursor = self.menu_stack[-1].cursor
        item = menu[cursor] if cursor < len(menu) else None
        return menu , cursor , item

    def set_Current(self , cursor = None , item = None):
        menu , cursor , _ = self.get_Current()
        if item:
            if cursor < len(menu):
                self.menu_stack[-1].menu[cursor] = item
            else:
                raise IndexError(f"Cursor value of {cursor} is outside of bounds for menu with length {len(menu)}.")
        if cursor:
            self.menu_stack[-1].cursor = cursor
        
    def do_Input(self , turns , pressed):
        result = self._make_Cursor_Valid()
        if result.bad:
            return result
        
        _ , _ , item = self.get_Current()

        item_type = item.i_type

        if item_type == m.Item_Type.NUM_SELECT:
            self._num_Select(turns , pressed)
        elif item_type == m.Item_Type.LEAF:
            self._leaf(turns , pressed)

    def _num_Select(self , turns , pressed):
        _ , _ , item = self.get_Current()
        if item.editing:
            if pressed:
                item.editing = False
                return
            item.value += turns * item.step
            self.set_Current(item=item)
        else:
            self._navigate(turns)

    def _leaf(self , turns , pressed):
        if pressed:
            _ , _ , item = self.get_Current()
            try: 
                return Result.success()
            except Exception as e:
                return Result.error(message=f"Error doing {item.name}. Error was: {e}.")
        else:
            self._navigate()
            return Result.success()

    def _navigate(self , turns):
        _ , cursor , _ = self.get_Current()
        cursor = cursor + turns
        self.set_Current(cursor=cursor)

    def _make_Cursor_Valid(self):
        menu , cursor , _ = self.get_Current()

        num_items = len(menu)

        def put_In_Menu(cursor):
            if cursor >= num_items:
                cursor = 0
            return cursor

        cursor = put_In_Menu(cursor)

        for _ in range(num_items):
            if menu[cursor].cursor:
                break
            else:
                cursor += 1
                cursor = put_In_Menu(cursor)
            return Result.error(message="The menu at the end of the stack has no valid cursor locations.")

        self.menu_stack[-1] = Menu_Frame(menu=menu , cursor=cursor)
        return Result.success()

def main_Menu(print_session):

    title = m.Title("Main Menu")
    num_select = m.Num_Select("Select Number: " , step = .5)
    print = m.Leaf("Print")

    print.action = lambda: print(num_select.value)

    return [title , num_select , print]
    
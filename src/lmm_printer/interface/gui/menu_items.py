from dataclasses import dataclass
from collections.abc import Callable
import pygame
from lmm_printer.core.types import Result

@dataclass
class Theme:
    height: int = 24
    outline_t: int = 1
    font: pygame.font.Font = None
    gaps: int = 5
    checkbox_size: int = 12
    checkbox_t: int = 1
    checkbox_button_size: int = 6
    body_color: str = "#9cafb7"
    outline_color: str = "#231b1b"
    text_color: str = "#231b1b"
    checkbox_color: str = "#231b1b"
    checkbox_button_color: str = "#ff8811"

@dataclass
class Selected_Theme(Theme):
    body_color: str = "#d64550"
    outline_color: str = "#231b1b"
    text_color: str = "#231b1b"
    checkbox_color: str = "#231b1b"
    checkbox_button_color: str = "#ff8811"

@dataclass
class Captured_Theme(Theme):
    body_color: str = "#ff8811"
    outline_color: str = "#231b1b"
    text_color: str = "#231b1b"
    checkbox_color: str = "#231b1b"
    checkbox_button_color: str = "#ff8811"

@dataclass(eq=False)
class Item:
    label: str = "Unknown Label"
    cursor: bool = True
    captured: bool = False

    def on_Press(self , handler):
        return
    def on_Turn(self , turns):
        return
    def draw_Panel(self , canvas , theme):
        width , height = canvas.get_size()
        pygame.draw.rect(canvas , theme.body_color , pygame.Rect(0 , 0 , width , height))
        pygame.draw.rect(canvas , theme.outline_color , canvas.get_rect() , width=theme.outline_t)
    def center(self , canvas , surface):
        width , height = canvas.get_size()
        surf_width , surf_height = surface.get_size()
        width_spacing = (width - surf_width) // 2
        height_spacing = (height - surf_height) // 2
        return width_spacing , height_spacing
    def draw(self , canvas , selected , themes):
        theme = themes[selected]
        self.draw_Panel(canvas , theme)
        text = theme.font.render(self.label , True , theme.text_color)
        text_x , text_y = self.center(canvas , text)
        canvas.blit(text , (text_x , text_y))

@dataclass(eq=False)
class Leaf(Item):
    action: Callable = None

    def on_Press(self , handler):
        try:
            return Result.success(value=self.action())
        except Exception as e:
            return Result.error(message=f"Error doing action of {self.label}. Error was {e}.")
        
@dataclass(eq=False)
class Branch(Item):
    sub_menu: Callable = None

    def on_Press(self , handler):
        try:
            sub_menu = self.sub_menu()
            handler.push(sub_menu)
            return Result.success()
        except Exception as e:
            return Result.error(message=f"Error doing the pushing sub menu of {self.label}. Error was {e}.")

@dataclass(eq=False)
class Title(Item):
    cursor: bool = False

@dataclass(eq=False)
class Num_Select(Item):
    value: float = 0
    step: float = 1

    def on_Press(self , handler):
        self.captured = not self.captured
    def on_Turn(self, turns):
        if self.captured:
            self.value += turns*self.step
    def draw(self , canvas , selected , themes):
        theme = themes[selected + self.captured]
        self.draw_Panel(canvas , theme)
        text = theme.font.render(self.label , True , theme.text_color)
        text_x , text_y = self.center(canvas , text)
        canvas.blit(text , (theme.gaps + theme.outline_t , text_y))
        value_text = theme.font.render(f"{self.value:.2f}" , True , theme.text_color)
        canvas.blit(value_text , (2*theme.gaps + theme.outline_t + text.get_width() , text_y))
    
@dataclass(eq=False)
class Checkbox(Item):
    is_checked: bool = False

    def on_Press(self , handler):
        self.captured = not self.captured
    def on_Turn(self, turns):
        if self.captured:
            self.is_checked = not self.is_checked
    def draw_Checkbox(self , canvas , theme):
        width , height = canvas.get_size()
        box_size = theme.checkbox_size
        box_t = theme.checkbox_t
        button_size = theme.checkbox_button_size
        gaps = theme.gaps
        t = theme.outline_t
        box_x = width - t - gaps - 2*box_t - box_size
        box_y = (height // 2) - (box_size // 2)  
        pygame.draw.rect(canvas , theme.checkbox_color , pygame.Rect(box_x , box_y , box_size , box_size) , width = box_t)
        if self.is_checked:
            button_x = box_x + (box_size - button_size)//2
            button_y = box_y + (box_size - button_size)//2
            pygame.draw.rect(canvas , theme.checkbox_button_color , pygame.Rect(button_x , button_y , button_size , button_size))
    def draw(self , canvas , selected , themes):
        theme = themes[selected + self.captured]
        self.draw_Panel(canvas , theme)
        text = theme.font.render(self.label , True , theme.text_color)
        text_x , text_y = self.center(canvas , text)
        canvas.blit(text , (theme.gaps + theme.outline_t , text_y))
        self.draw_Checkbox(canvas , theme)


@dataclass(eq=False)
class Back(Item):
    def on_Press(self, handler):
        handler.pop()
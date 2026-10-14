from dataclasses import dataclass
from collections.abc import Callable
from enum import Enum
from typing import Generic , TypeVar
import pygame

T = TypeVar("T")

@dataclass
class Theme:
    body_color: list = [0 , 0 , 0] 
    outline_color: list = [210 , 210 , 210]
    text_color: list = [128 , 128 , 128]
    outline_t: int = 3
    font: pygame.font.Font = pygame.font.Font(None , 24)

class Selected_Theme(Theme):
    body_color: list = [10 , 10 , 10] 
    outline_color: list = [255 , 255 , 255]
    text_color: list = [128 , 128 , 128]

@dataclass(eq=False)
class Item(Generic[T]):
    label: str = "Unknown Label"
    cursor: bool = True
    captured: bool = False
    themes: tuple = (Theme() , Selected_Theme())

    def on_Press(self , handler):
        return
    def on_Turn(self , turns):
        return
    def draw_Panel(self , canvas , theme):
        width , height = canvas.get_size()
        pygame.draw.rect(canvas , theme.body_color , pygame.rect(0 , 0 , width , height))
        pygame.draw.rect(canvas , theme.outline_color , pygame.rect(theme.outline_t , theme.outline_t , width-theme.outline_t , height-theme.outline_t) , width=theme.outline_t)
    def center(self , canvas , surface):
        width , height = canvas.get_size()
        surf_width , surf_height = surface.get_size()
        width_spacing = (width - surf_width) // 2
        height_spacing = (height - surf_height) // 2
        return width_spacing , height_spacing
    def draw(self , canvas , selected):
        theme = self.themes[selected]
        self.draw_Panel(canvas , theme)
        text = theme.font.render(self.label , True , theme.text_color)
        text_x , text_y = self.center(canvas , text)
        canvas.blit(text , (text_x , text_y))

@dataclass(eq=False)
class Leaf(Item):
    action: Callable = None

@dataclass(eq=False)
class Branch(Item):
    submenu: Callable = None

@dataclass(eq=False)
class Title(Item):
    cursor: bool = False

@dataclass(eq=False)
class Num_Select(Item):
    value: float = 0
    step: float = 1
    
@dataclass(eq=False)
class Checkbox(Item):
    is_checked: bool = False
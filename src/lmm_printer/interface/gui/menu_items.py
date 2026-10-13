from dataclasses import dataclass
from collections.abc import Callable
from enum import Enum
from typing import Generic , TypeVar

T = TypeVar("T")

class Item_Type(Enum):
    GENERIC = "generic"
    LEAF = "leaf" # Does something and 
    BRANCH = "branch"
    TITLE = "title"
    NUM_SELECT = "num_select"
    CHECK_BOX = "check_box"

@dataclass
class Item(Generic[T]):
    label: str = "Unknown Label"
    i_type: Item_Type = Item_Type.GENERIC
    cursor: bool = True

@dataclass 
class Editiable_Item(Item):
    editing: bool = False

@dataclass
class Leaf(Item):
    i_type: Item_Type = Item_Type.LEAF
    action: Callable = None

@dataclass
class Branch(Item):
    i_type: Item_Type = Item_Type.BRANCH
    action: Callable = None
    submenu: Callable = None

@dataclass
class Title(Item):
    cursor: bool = False

@dataclass
class Num_Select(Editiable_Item):
    i_type: Item_Type = Item_Type.NUM_SELECT
    value: float = 0
    step: float = 1
    
@dataclass
class Check_Box(Editiable_Item):
    i_type: Item_Type = Item_Type.CHECK_BOX
    is_checked: bool = False
from dataclasses import dataclass
from collections.abc import Callable
from enum import Enum
from typing import Generic , TypeVar

T = TypeVar("T")

class M_Item_Type(Enum):
    LEAF = "leaf" # Does something and 
    BRANCH = "branch"
    TITLE = "title"
    NUM_SELECT = "num_select"
    CHECK_BOX = "check_box"


@dataclass
class M_Item(Generic[T]):
    label: str = "Unknown Label"
    m_type: M_Item_Type = M_Item_Type.TITLE
    action: Callable = None
    value: T = None


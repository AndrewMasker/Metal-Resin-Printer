import numpy as np
import os
import re
from dataclasses import dataclass , field
from enum import Enum
from typing import Generic , TypeVar
import zipfile
import json
from PIL import Image
import io

T = TypeVar("T")

class State(Enum):
    SUCCESS = "success"
    ERROR = "error"

@dataclass
class Result(Generic[T]):
    value: T
    message: str = ""
    state: State = State.SUCCESS

@dataclass
class Printer_State:
    pos: list = field(default_factory=lambda:[0 , 0 , 0])
    safe_shutdown: bool = False

class NanoDLP_File:
    def __init__(self , path):
        self._zip = zipfile.ZipFile(path)

    def get_Image(self , id):
        with self._zip.open(str(id) + ".png") as f:
            image = Image.open(io.BytesIO(f.read()))
        
        try:
            image = np.array(image)
            image = image.reshape(image.shape[0] , image.shape[1]*3)
            image = np.flip(image , axis = 0)
            return Result(value = image , state = State.SUCCESS , message = "Successfully decoded image.")
        except Exception as e:
            return Result(value = None , state = State.ERROR , message = "Likely one of the image dimensions isn't divisible by 3 (for nanodlp). Try to flip axes in slicer. Error was: " + str(e)) 

    def get_Num_Layers(self):
        return len([
            n for n in self._zip.namelist() 
            if re.fullmatch(r"\d+\.png" , os.path.basename(n).lower())
        ])

    def get_Options(self):
        try:
            with self._zip.open("options.json") as f:
                options = json.load(f)
            with self._zip.open("profile.json") as f:
                profile = json.load(f)
            options = {"exposure_time": profile["CureTime"] , "layer_thickness": options["Thickness"]*.001}
            return Result(value = options , state = State.SUCCESS , message = "Successfully loaded options.")
        except Exception as e:
            return Result(value = None , state = State.ERROR , message = "Couldn't open options.json. Error was: " + str(e))

    def close(self):
        self._zip.close()

    def __enter__(self):
        return self
    
    def __exit__(self , *exc):
        self.close()

class Print_File:
    def __init__(self , path):
        self._backend = NanoDLP_File(path)

    def get_Image(self , id):
        return self._backend.get_Image(id)

    def get_Num_Layers(self):
        return self._backend.get_Num_Layers()

    def get_Options(self):
        return self._backend.get_Options()

    def close(self):
        self._backend.close()

    def __enter__(self):
        return self

    def __exit__(self , *exc):
        self.close()

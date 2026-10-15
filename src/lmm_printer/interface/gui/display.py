import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
import glob , os

class Framebuffer:
    def __init__(self , path , size):
        self.fd = os.open(path , os.O_RDWR)
        self.out = pygame.Surface(size , depth = 16 , masks = (0xF800 , 0x07E0 , 0x001F , 0))

    def show(self , canvas):
        self.out.blit(canvas , (0 , 0))
        os.pwrite(self.fd , self.out.get_buffer().raw , 0)

def find_Panel(match = "mipi"):
    for name_file in sorted(glob.glob("/sys/class/graphics/fb*/name")):
        with open(name_file) as f:
            if match in f.read():
                return "/dev/" + os.path.basename(os.path.dirname(name_file))
    raise FileNotFoundError
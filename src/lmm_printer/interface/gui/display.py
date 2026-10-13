import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

class Framebuffer:
    def __init__(self , path , size):
        self.fd = os.open(path , os.O_RDWR)
        self.out = pygame.Surface(size , depth = 16 , masks = (0xF800 , 0x07E0 , 0x001F , 0))

    def show(self , canvas):
        self.out.blit(canvas , (0 , 0))
        os.pwrite(self.fd , self.out.get_buffer().raw , 0)
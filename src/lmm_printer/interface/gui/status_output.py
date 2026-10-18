from lmm_printer.core.types import Session_Status , NUM_AXES , NUM_PROBES , AXIS_NAMES , PROBE_NAMES
import pygame

class Status_Output:
    def __init__(self , theme):
        self.first_set = True
        self.status = Session_Status()
        self.theme = theme

    def set_Status(self , status):
        if self.first_set:
            self.first_set = False
            self.status = status
            return True
        if self.status == status:
            return False
        else:
            self.status = status
            return True

    def draw(self , canvas):
        lines = []
        hard_conn = self.status.hardware_connected
        lines.append(f"Hardware: {hard_conn}")
        for axis_id in range(NUM_AXES):
            lines.append(f"{AXIS_NAMES[axis_id].title()}: {self.status.state.pos[axis_id] if hard_conn else '*'}")
        for probe_id in range(NUM_PROBES):
            lines.append(f"{PROBE_NAMES[probe_id].title()}: {self.status.state.temps[probe_id] if hard_conn else '*'}")
        lines.append(f"File: {self.status.file_name if self.status.file_name is not None else 'None'}")
        lines.append(f"Layer: {self.status.current_layer if self.status.current_layer is not None else '*'}/{self.status.num_layers if self.status.num_layers is not None else '*'}")
        lines.append(f"Printing: {self.status.printing}")

        text_list = []
        offset_list = []
        offset = 0
        for line in lines:
            text = self.theme.font.render(line , True , self.theme.text_color)
            text_list.append(text)
            offset_list.append(offset)
            offset += text.get_height()

        for i , text in enumerate(text_list):
            rect = pygame.Rect(0 , offset_list[i] , canvas.get_width() , text.get_height())
            if not canvas.get_rect().contains(rect): continue
            canvas.blit(text , (self.theme.gaps , offset_list[i]))
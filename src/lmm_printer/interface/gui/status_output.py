from lmm_printer.core.types import Session_Status , NUM_AXES , NUM_PROBES , AXIS_NAMES , PROBE_NAMES
import pygame
import time

class Status_Output:
    def __init__(self , theme , step_period = 1.5):
        self.first_set = True
        self.status = Session_Status()
        self.theme = theme

        self.step_period = step_period
        self.scroll_index = 0
        self.last_step_time = 0
        self.overflowing = False

    def set_Status(self , status):
        changed = self.first_set or self.status != status
        self.first_set = False
        self.status = status

        now = time.monotonic()
        if self.overflowing and (now - self.last_step_time) >= self.step_period:
            self.last_step_time = now
            self.scroll_index += 1
            changed = True
        return changed

    def _get_Initials(self , string):
        if len(string.split())>1:
            initials = "".join(word[0].upper() for word in string.split()) 
        else:
            initials = "".join(word[:3].upper() for word in string.split())
        return initials

    def _build_Lines(self):
        lines = []
        hard_conn = self.status.hardware_connected
        for axis_id in range(NUM_AXES):
            val = f"{self.status.state.pos[axis_id]:.1f}" if hard_conn else '*'
            lines.append(f"{self._get_Initials(AXIS_NAMES[axis_id])}: {val}")
        for probe_id in range(NUM_PROBES):
            val = f"{self.status.state.temps[probe_id]:.1f}" if hard_conn else '*'
            lines.append(f"{self._get_Initials(PROBE_NAMES[probe_id])}: {val}")
        lines.append(f"File: {self.status.file_name if self.status.file_name is not None else 'None'}")
        lines.append(f"Layer: {self.status.current_layer if (self.status.current_layer is not None and self.status.printing) else '*'}/{self.status.num_layers if self.status.num_layers is not None else '*'}")
        return lines

    def draw(self , canvas):
        lines = self._build_Lines()
        line_h = self.theme.font.get_height()
        num_visible = canvas.get_height() // line_h
        self.overflowing = len(lines) > num_visible

        if self.overflowing:
            lines = lines + [""]
            start = self.scroll_index % len(lines)
            visible_lines = [lines[(start + k) % len(lines)] for k in range(num_visible)]
        else:
            visible_lines = lines

        for k , line in enumerate(visible_lines):
            text = self.theme.font.render(line , True , self.theme.text_color)
            canvas.blit(text , (self.theme.gaps , k * line_h))

        
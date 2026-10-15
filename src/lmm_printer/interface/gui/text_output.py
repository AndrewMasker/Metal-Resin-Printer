import pygame

class Text_Output:
    def __init__(self , max_lines , theme):
        self.lines = []
        self.max_lines = max_lines
        self.theme = theme

    def push(self , line):
        self.lines.append(line)
        if len(self.lines) > self.max_lines:
            self.lines.pop(0)

    def draw(self , canvas):
        width , height = canvas.get_size()

        text_height = 0
        text_list = []
        for line in self.lines:
            text = self.theme.font.render(line , True , self.theme.text_color)
            line_height = text.get_height()
            text_height += line_height
            text_list.append(text)

        offset = 0
        if text_height > height:
            offset = -(text_height - height)

        item_depth = 0
        for text in text_list:
            item_offset = item_depth + offset
            rect = pygame.Rect(0 , item_offset , width , line_height)
            item_depth += line_height
            if not canvas.get_rect().contains(rect): continue
            canvas.blit(text , (self.theme.gaps , item_offset))

      
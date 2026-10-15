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

        text_heights = []
        text_list = []
        for line in self.lines:
            text = self.theme.font.render(line , True , self.theme.text_color)
            text_heights.append(text.get_height())
            text_list.append(text)
        text_height = sum(text_heights)

        offset = 0
        if text_height > height:
            offset = -(text_height - height)

        item_depth = 0
        for i , text in enumerate(text_list):
            item_offset = item_depth + offset
            rect = pygame.Rect(0 , item_offset , width , text_heights[i])
            item_depth += text_heights[i]
            if not canvas.get_rect().contains(rect): continue
            canvas.blit(text , (self.theme.gaps , item_offset))

      
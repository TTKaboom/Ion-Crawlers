import pygame

class Button:
    def __init__(self, x, y, w, h, text, font, bg_color=(40, 40, 50), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.base_color = bg_color
        self.text_color = text_color
        self.is_hovered = False

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, screen, is_active=False):
        # Draw background fill
        if is_active:
            color = (33, 150, 243)  # Bright Active Cyan
        elif self.is_hovered:
            color = tuple(min(255, c + 30) for c in self.base_color)  # Lighter tint
        else:
            color = self.base_color

        pygame.draw.rect(screen, color, self.rect, border_radius=6)

        # White highlight border for active selections
        border_color = (255, 255, 255) if (is_active or self.is_hovered) else (70, 70, 80)
        pygame.draw.rect(screen, border_color, self.rect, width=2, border_radius=6)

        # Draw centered text label
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)


class TextInput:
    def __init__(self, x, y, w, h, font, placeholder=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.placeholder = placeholder
        self.text = ""
        self.is_focused = False
        self.cursor_visible = True
        self.cursor_timer = 0.0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.is_focused = self.rect.collidepoint(event.pos)

        elif event.type == pygame.KEYDOWN and self.is_focused:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif len(self.text) < 10:  # Cap length of map seed to 10 characters
                if event.unicode.isdigit():  # Seeds are digits only
                    self.text += event.unicode

    def update(self, dt):
        if self.is_focused:
            self.cursor_timer += dt
            if self.cursor_timer >= 0.5:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0.0
        else:
            self.cursor_visible = False

    def draw(self, screen):
        bg_color = (25, 25, 35) if self.is_focused else (15, 15, 20)
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=6)

        border_color = (33, 150, 243) if self.is_focused else (50, 50, 60)
        pygame.draw.rect(screen, border_color, self.rect, width=2, border_radius=6)

        # Text or placeholder drawing
        if not self.text and not self.is_focused:
            text_surf = self.font.render(self.placeholder, True, (100, 100, 110))
        else:
            text_surf = self.font.render(self.text, True, (240, 240, 250))

        screen.blit(text_surf, (self.rect.x + 10, self.rect.y + (self.rect.h - text_surf.get_height()) // 2))

        # Blit text input cursor
        if self.is_focused and self.cursor_visible:
            cursor_x = self.rect.x + 10 + text_surf.get_width() + 2
            cursor_y = self.rect.y + 6
            pygame.draw.line(screen, (33, 150, 243), (cursor_x, cursor_y), (cursor_x, cursor_y + self.rect.h - 12), 2)

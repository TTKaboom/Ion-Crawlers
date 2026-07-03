import pygame

class Scene:
    def __init__(self, manager: 'SceneManager'):
        """Store a reference to the manager so the scene can trigger transitions."""
        self.manager = manager

    def handle_event(self, event: pygame.event.Event) -> None:
        """Process player inputs (mouse clicks, key presses)."""
        pass

    def update(self, dt: float) -> None:
        """Update scene logic, timers, or animations (dt = seconds since last frame)."""
        pass

    def draw(self, screen: pygame.Surface) -> None:
        """Render shapes, text, and placeholders onto the screen."""
        pass


class SceneManager:
    def __init__(self):
        self.current_scene: Scene | None = None

    def change_scene(self, new_scene: Scene) -> None:
        """Smoothly switch the active scene to a new one."""
        self.current_scene = new_scene

    def handle_event(self, event: pygame.event.Event) -> None:
        """Delegate event processing to the active scene."""
        if self.current_scene:
            self.current_scene.handle_event(event)

    def update(self, dt: float) -> None:
        """Delegate logic updates to the active scene."""
        if self.current_scene:
            self.current_scene.update(dt)

    def draw(self, screen: pygame.Surface) -> None:
        """Delegate rendering to the active scene."""
        if self.current_scene:
            self.current_scene.draw(screen)

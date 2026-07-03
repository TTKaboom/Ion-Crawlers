import pygame
import game.gui.scene
from game.gui.scene import SceneManager
import game.gui.scenes.title_scene as ts

def main():
    pygame.init()
    #screen = pygame.display.set_mode((500, 400))
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Ion Crawler")
    clock = pygame.time.Clock()

    # Create the manager and set the starting scene
    manager = SceneManager()
    manager.change_scene(ts.TitleScene(manager))

    running = True
    while running:
        # 1. Delta Time (seconds elapsed since last frame)
        dt = clock.tick(60) / 1000.0  # Cap at 60 FPS

        # 2. Event Handling Loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            manager.handle_event(event)

        # 3. Logic Update
        manager.update(dt)

        # 4. Drawing
        manager.draw(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()

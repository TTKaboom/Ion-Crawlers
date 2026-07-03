from __future__ import annotations

import pygame
from pathlib import Path

# Core logic imports from your engine
from game.enums import GameMode, Difficulty, ChargeVisibility
from game.engine import RunConfig, GameEngine
from game.gui.scene import Scene, SceneManager
from game.gui.colors import Colors  # Simple dict of (R, G, B) tuples
from game.gui.ui import Button, TextInput


class TitleScene(Scene):
    def __init__(self, manager: SceneManager):
        super().__init__(manager)

        # Default starting configurations
        self.selected_mode = GameMode.MIXED
        self.selected_difficulty = Difficulty.EASY
        self.selected_visibility = ChargeVisibility.BOTH

        # Load standard fonts
        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.label_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.help_font = pygame.font.SysFont("Arial", 14, italic=True)

        # 1. Initialize Mode Selector Buttons
        self.mode_buttons = {
            GameMode.ANION: Button(300, 160, 120, 35, "Anion Mode", self.label_font),
            GameMode.CATION: Button(430, 160, 120, 35, "Cation Mode", self.label_font),
            GameMode.MIXED: Button(560, 160, 120, 35, "Mixed Mode", self.label_font),
        }

        # 2. Initialize Difficulty Selector Buttons
        self.diff_buttons = {
            Difficulty.EASY: Button(300, 230, 120, 35, "Easy (12 HP)", self.label_font),
            Difficulty.MEDIUM: Button(430, 230, 120, 35, "Medium (8 HP)", self.label_font),
            Difficulty.HARD: Button(560, 230, 120, 35, "Hard (5 HP)", self.label_font),
        }

        # 3. Initialize Visibility Selector Buttons
        self.vis_buttons = {
            ChargeVisibility.BOTH: Button(300, 300, 90, 35, "Both", self.label_font),
            ChargeVisibility.SPELLS_ONLY: Button(400, 300, 100, 35, "Spells Only", self.label_font),
            ChargeVisibility.MONSTERS_ONLY: Button(510, 300, 110, 35, "Monsters Only", self.label_font),
            ChargeVisibility.NEITHER: Button(630, 300, 90, 35, "Neither", self.label_font),
        }

        # 4. Interactive Seed Text Input Box
        self.seed_input = TextInput(300, 370, 240, 35, self.label_font, placeholder="Random Seed")

        # 5. Huge Big Start Button
        self.start_button = Button(300, 480, 200, 50, "START RUN", self.title_font, bg_color=(46, 125, 50))

    def handle_event(self, event: pygame.event.Event) -> None:
        # Pass keyboard events to the text box for seed inputs
        self.seed_input.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Handle Game Mode selection clicks
            for mode, btn in self.mode_buttons.items():
                if btn.rect.collidepoint(mouse_pos):
                    self.selected_mode = mode

            # Handle Difficulty selection clicks
            for diff, btn in self.diff_buttons.items():
                if btn.rect.collidepoint(mouse_pos):
                    self.selected_difficulty = diff

            # Handle Visibility selection clicks
            for vis, btn in self.vis_buttons.items():
                if btn.rect.collidepoint(mouse_pos):
                    self.selected_visibility = vis

            # Handle START RUN button click
            if self.start_button.rect.collidepoint(mouse_pos):
                self._start_game_run()

    def update(self, dt: float) -> None:
        # Hover effect updates
        mouse_pos = pygame.mouse.get_pos()

        # Update button hover states
        for btn in list(self.mode_buttons.values()) + list(self.diff_buttons.values()) + list(
                self.vis_buttons.values()):
            btn.check_hover(mouse_pos)
        self.start_button.check_hover(mouse_pos)
        self.seed_input.update(dt)

    def draw(self, screen: pygame.Surface) -> None:
        # Fill deep dark space background
        screen.fill((18, 18, 24))

        # --- HEADER ---
        title_surf = self.title_font.render("ION CRAWLER", True, (230, 230, 250))
        sub_surf = self.help_font.render("An Educational Dungeon Crawler on Chemical Neutralization", True,
                                         (150, 150, 180))
        screen.blit(title_surf, (800 // 2 - title_surf.get_width() // 2, 40))
        screen.blit(sub_surf, (800 // 2 - sub_surf.get_width() // 2, 100))

        # --- LABELS ---
        mode_label = self.label_font.render("Game Mode:", True, (200, 200, 220))
        diff_label = self.label_font.render("Difficulty:", True, (200, 200, 220))
        vis_label = self.label_font.render("Visibility:", True, (200, 200, 220))
        seed_label = self.label_font.render("Map Seed:", True, (200, 200, 220))

        screen.blit(mode_label, (100, 165))
        screen.blit(diff_label, (100, 235))
        screen.blit(vis_label, (100, 305))
        screen.blit(seed_label, (100, 375))

        # --- DRAW SELECTION BUTTONS & VISUAL HIGHLIGHTS ---
        for mode, btn in self.mode_buttons.items():
            btn.draw(screen, is_active=(mode == self.selected_mode))

        for diff, btn in self.diff_buttons.items():
            btn.draw(screen, is_active=(diff == self.selected_difficulty))

        for vis, btn in self.vis_buttons.items():
            btn.draw(screen, is_active=(vis == self.selected_visibility))

        # Draw the Seed Input box
        self.seed_input.draw(screen)

        # Draw the START RUN button
        self.start_button.draw(screen)

    def _start_game_run(self) -> None:
        # Convert seed string to integer if possible, else use random (None)
        raw_seed = self.seed_input.text.strip()
        seed = None
        if raw_seed.isdigit():
            seed = int(raw_seed)

        # Construct the game engine config
        config = RunConfig(
            mode=self.selected_mode,
            difficulty=self.selected_difficulty,
            visibility=self.selected_visibility,
            csv_path=Path("ions.csv"),
            rng_seed=seed
        )

        # Instantiate and initialize the engine
        engine = GameEngine(config)

        # Import the DungeonScene dynamically to avoid circular import issues
        from game.gui.scenes.dungeon_scene import DungeonScene

        # Switch directly to the active Dungeon Crawler view
        self.manager.change_scene(DungeonScene(self.manager, engine, 1024,768))
from __future__ import annotations

import pygame
from game.enums import RoomType
from game.engine import GameEngine
from game.gui.scene import Scene, SceneManager
from game.gui.colors import Colors
from game.gui.ui import Button


class DungeonScene(Scene):
    def __init__(self, manager: SceneManager, engine: GameEngine, screen_height: int, screen_width: int):
        super().__init__(manager)
        self.engine = engine
        self.engine.setup()
        self.screen_height = screen_height
        self.screen_width = screen_width
        self.player = engine.state.player
        self.dungeon = engine.dungeon
        self.previous_position = self.player.position

        # Setup fonts (scaled slightly with screen size if desired)
        self.header_font = pygame.font.SysFont("Arial", int(self.screen_height * 0.04), bold=True)
        self.text_font = pygame.font.SysFont("Arial", int(self.screen_height * 0.026), bold=True)
        self.desc_font = pygame.font.SysFont("Arial", int(self.screen_height * 0.023))

        # --- DYNAMIC GRID & HUD GEOMETRY ---
        # Map pane takes up 56% of screen width, HUD takes remaining 44%
        self.map_area_width = int(self.screen_width * 0.56)
        self.hud_area_width = self.screen_width - self.map_area_width
        self.padding = int(self.screen_height * 0.025)  # e.g., ~19px at 768h

        # Centered Grid Boundary Box within Map Area
        max_grid_w = self.map_area_width - (self.padding * 4)
        max_grid_h = self.screen_height - (self.padding * 4)
        self.tile_spacing = int(self.screen_height * 0.013)  # e.g., ~10px at 768h

        grid_cols, grid_rows = self.dungeon.width, self.dungeon.height

        # Compute maximum square tile size
        self.tile_size = min(
            (max_grid_w - (grid_cols - 1) * self.tile_spacing) // grid_cols,
            (max_grid_h - (grid_rows - 1) * self.tile_spacing) // grid_rows
        )

        # Calculate actual bounding size of drawn grid
        grid_pixel_w = grid_cols * self.tile_size + (grid_cols - 1) * self.tile_spacing
        grid_pixel_h = grid_rows * self.tile_size + (grid_rows - 1) * self.tile_spacing

        # Offset to perfectly center grid in left pane
        self.grid_offset_x = (self.map_area_width - grid_pixel_w) // 2
        self.grid_offset_y = (self.screen_height - grid_pixel_h) // 2

        # --- MODAL POSITIONS (CENTERED IN THE LEFT MAP AREA) ---
        self.modal_w = int(self.map_area_width * 0.7)
        self.modal_h = int(self.screen_height * 0.35)
        self.modal_x = (self.map_area_width - self.modal_w) // 2
        self.modal_y = (self.screen_height - self.modal_h) // 2

        # Interactive Modals States
        self.chest_modal_open = False
        self.gained_spell = None
        self.chest_dismiss_btn = None

        self.exit_modal_open = False
        self.exit_yes_btn = None
        self.exit_no_btn = None

    def handle_event(self, event: pygame.event.Event) -> None:
        # Modal Interactivity First
        if self.chest_modal_open:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.chest_dismiss_btn and self.chest_dismiss_btn.rect.collidepoint(event.pos):
                    self.chest_modal_open = False
            elif event.type == pygame.KEYDOWN and event.key in {pygame.K_SPACE, pygame.K_RETURN}:
                self.chest_modal_open = False
            return

        if self.exit_modal_open:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.exit_yes_btn and self.exit_yes_btn.rect.collidepoint(event.pos):
                    self._complete_run()
                elif self.exit_no_btn and self.exit_no_btn.rect.collidepoint(event.pos):
                    self.exit_modal_open = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    self._complete_run()
                elif event.key == pygame.K_n:
                    self.exit_modal_open = False
            return

        # Keyboard Exploration
        if event.type == pygame.KEYDOWN:
            direction = None
            if event.key in {pygame.K_UP, pygame.K_w}:
                direction = "n"
            elif event.key in {pygame.K_DOWN, pygame.K_s}:
                direction = "s"
            elif event.key in {pygame.K_LEFT, pygame.K_a}:
                direction = "w"
            elif event.key in {pygame.K_RIGHT, pygame.K_d}:
                direction = "e"

            if direction:
                self._try_move_player(direction)

        # Mouse Click Grid Navigation
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked_coord = self._get_grid_coord_from_pixels(event.pos)
            if clicked_coord:
                px, py = self.player.position
                cx, cy = clicked_coord
                if abs(px - cx) + abs(py - cy) == 1:
                    if cx > px:
                        self._try_move_player("e")
                    elif cx < px:
                        self._try_move_player("w")
                    elif cy > py:
                        self._try_move_player("s")
                    elif cy < py:
                        self._try_move_player("n")

    def update(self, dt: float) -> None:
        mouse_pos = pygame.mouse.get_pos()
        if self.chest_modal_open and self.chest_dismiss_btn:
            self.chest_dismiss_btn.check_hover(mouse_pos)
        elif self.exit_modal_open and self.exit_yes_btn and self.exit_no_btn:
            self.exit_yes_btn.check_hover(mouse_pos)
            self.exit_no_btn.check_hover(mouse_pos)

        if self.engine.is_run_over() and not self.chest_modal_open and not self.exit_modal_open:
            self._complete_run()

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(Colors.BG_DARK)

        # --- DRAW VISUAL GRID MAP ---
        self._draw_grid_map(screen)

        # --- DRAW HUD PANEL ---
        self._draw_hud_panel(screen)

        # --- DRAW ACTIVE OVERLAYS ---
        if self.chest_modal_open:
            self._draw_chest_modal(screen)
        elif self.exit_modal_open:
            self._draw_exit_modal(screen)

    # --- PRIVATE ENGINE RESOLUTION HELPERS ---

    def _try_move_player(self, direction: str) -> None:
        old_pos = self.player.position
        if self.engine.move_player(direction):
            self.previous_position = old_pos
            self._resolve_room_outcome()

    def _resolve_room_outcome(self) -> None:
        room_status = self.engine.resolve_current_room()

        if room_status == "monster":
            from game.gui.views.combat_scene import CombatScene
            self.manager.change_scene(CombatScene(self.manager, self.engine, self.previous_position))

        elif room_status == "chest":
            self.gained_spell = self.engine.grant_chest_reward()
            self.chest_modal_open = True

            # Dynamically compute size and center of Claim button
            btn_w, btn_h = int(self.modal_w * 0.4), int(self.modal_h * 0.16)
            btn_x = self.modal_x + (self.modal_w - btn_w) // 2
            btn_y = self.modal_y + int(self.modal_h * 0.7)
            self.chest_dismiss_btn = Button(btn_x, btn_y, btn_w, btn_h, "CLAIM", self.text_font, Colors.NEUTRAL_DARK)

            room = self.dungeon.room_at(self.player.position)
            room.chest_opened = True

        elif room_status == "exit":
            self.exit_modal_open = True
            btn_w, btn_h = int(self.modal_w * 0.35), int(self.modal_h * 0.16)
            btn_y = self.modal_y + int(self.modal_h * 0.7)

            self.exit_yes_btn = Button(self.modal_x + int(self.modal_w * 0.1), btn_y, btn_w, btn_h, "LEAVE (Y)",
                                       self.text_font, Colors.NEUTRAL_DARK)
            self.exit_no_btn = Button(self.modal_x + int(self.modal_w * 0.55), btn_y, btn_w, btn_h, "STAY (N)",
                                      self.text_font, Colors.CATION_DARK)

    # --- DYNAMIC DRAWING LOGIC ---

    def _draw_grid_map(self, screen: pygame.Surface) -> None:
        # Draw bounding border around Map Area
        border_rect = pygame.Rect(self.padding, self.padding, self.map_area_width - (2 * self.padding),
                                  self.screen_height - (2 * self.padding))
        pygame.draw.rect(screen, Colors.BORDER_DEFAULT, border_rect, width=2, border_radius=8)

        for y in range(self.dungeon.height):
            for x in range(self.dungeon.width):
                pos = (x, y)
                room = self.dungeon.room_at(pos)

                rx = self.grid_offset_x + x * (self.tile_size + self.tile_spacing)
                ry = self.grid_offset_y + y * (self.tile_size + self.tile_spacing)
                room_rect = pygame.Rect(rx, ry, self.tile_size, self.tile_size)

                if not room.visited and pos != self.dungeon.start_position and pos != self.dungeon.exit_position:
                    color = Colors.ROOM_FOG
                    label = "?"
                    text_color = Colors.TEXT_MUTED
                else:
                    if pos == self.dungeon.start_position:
                        color = Colors.ROOM_START
                        label = "START"
                        text_color = Colors.TEXT_HIGH
                    elif pos == self.dungeon.exit_position:
                        color = Colors.ROOM_EXIT
                        label = "EXIT"
                        text_color = Colors.TEXT_HIGH
                    elif room.room_type == RoomType.MONSTER and room.monster is not None:
                        color = Colors.ROOM_MONSTER
                        label = f"[{room.monster.ions[0].formula}]"
                        text_color = Colors.TEXT_HIGH
                    elif room.room_type == RoomType.CHEST and not room.chest_opened:
                        color = Colors.ROOM_CHEST
                        label = "CHEST"
                        text_color = Colors.TEXT_HIGH
                    else:
                        color = Colors.ROOM_EMPTY
                        label = "SAFE"
                        text_color = Colors.TEXT_MUTED

                pygame.draw.rect(screen, color, room_rect, border_radius=6)

                # Active room outline
                border_color = Colors.BORDER_ACTIVE if pos == self.player.position else Colors.BORDER_DEFAULT
                border_width = 3 if pos == self.player.position else 1
                pygame.draw.rect(screen, border_color, room_rect, width=border_width, border_radius=6)

                label_surf = self.desc_font.render(label, True, text_color)
                screen.blit(label_surf, label_surf.get_rect(center=room_rect.center))

                if pos == self.player.position:
                    pygame.draw.circle(screen, Colors.PLAYER_MARKER, room_rect.center, self.tile_size // 4)

    def _draw_hud_panel(self, screen: pygame.Surface) -> None:
        # Dynamic placement inside the right pane
        hud_x = self.map_area_width + self.padding
        hud_w = self.hud_area_width - (2 * self.padding)
        hud_h = self.screen_height - (2 * self.padding)

        panel_rect = pygame.Rect(hud_x, self.padding, hud_w, hud_h)
        pygame.draw.rect(screen, Colors.BORDER_DEFAULT, panel_rect, width=2, border_radius=8)

        hud_title = self.header_font.render("PLAYER HUD", True, Colors.TEXT_HIGH)
        screen.blit(hud_title, (hud_x + self.padding, self.padding + self.padding))

        # Graphical Health Bar
        hp_label = self.text_font.render("Health:", True, Colors.TEXT_MUTED)
        screen.blit(hp_label, (hud_x + self.padding, self.padding * 3.5))

        bar_y = int(self.padding * 4.6)
        bar_h = int(self.screen_height * 0.04)  # Proportional height of bar
        pygame.draw.rect(screen, Colors.BORDER_DEFAULT,
                         (hud_x + self.padding, bar_y, hud_w - (2 * self.padding), bar_h), border_radius=4)

        max_hp = self.engine.config.difficulty.starting_health
        pct = max(0.0, min(1.0, self.player.health / max_hp))
        fill_w = int((hud_w - (2 * self.padding) - 4) * pct)
        if fill_w > 0:
            fill_color = Colors.NEUTRAL_SUCCESS if pct > 0.4 else Colors.CATION_PRIMARY
            pygame.draw.rect(screen, fill_color, (hud_x + self.padding + 2, bar_y + 2, fill_w, bar_h - 4),
                             border_radius=2)

        hp_text = self.text_font.render(f"{self.player.health} / {max_hp}", True, Colors.TEXT_HIGH)
        screen.blit(hp_text,
                    (hud_x + hud_w // 2 - hp_text.get_width() // 2, bar_y + (bar_h - hp_text.get_height()) // 2))

        # Dynamic Stats Row placement
        stats_y = bar_y + bar_h + self.padding

        def draw_stat(label: str, val: str, y_offset: int):
            lbl_surf = self.desc_font.render(label, True, Colors.TEXT_MUTED)
            val_surf = self.text_font.render(val, True, Colors.TEXT_HIGH)
            screen.blit(lbl_surf, (hud_x + self.padding, y_offset))
            screen.blit(val_surf, (hud_x + int(hud_w * 0.5), y_offset))

        draw_stat("Game Mode:", self.engine.config.mode.name.upper(), stats_y)
        draw_stat("Difficulty:", self.engine.config.difficulty.name.upper(), stats_y + int(self.padding * 1.2))
        draw_stat("Visibility:", self.engine.config.visibility.name.upper(), stats_y + int(self.padding * 2.4))
        draw_stat("Score Base:", f"{self.player.total_charge_offset}", stats_y + int(self.padding * 3.6))

        # Spellbook list
        spell_lbl_y = stats_y + int(self.padding * 5.2)
        spell_label = self.text_font.render("Spellbook Inventory:", True, Colors.TEXT_MUTED)
        screen.blit(spell_label, (hud_x + self.padding, spell_lbl_y))

        show_spells = self.engine.config.visibility.name.lower() in {"both", "spells_only"}
        available_spells = self.player.available_spells()

        start_y = spell_lbl_y + int(self.padding * 1.6)
        card_h = int(self.screen_height * 0.045)  # Responsive height

        # Calculate how many spells we can draw dynamically without overflow
        max_spells_to_draw = (hud_h - (start_y - self.padding) - self.padding) // (card_h + 6)

        if not available_spells:
            no_spells_surf = self.desc_font.render("(No spells remaining!)", True, Colors.CATION_PRIMARY)
            screen.blit(no_spells_surf, (hud_x + self.padding, start_y))
        else:
            for idx, spell in enumerate(available_spells[:max_spells_to_draw]):
                sc_rect = pygame.Rect(hud_x + self.padding, start_y + idx * (card_h + 6), hud_w - (2 * self.padding),
                                      card_h)
                pygame.draw.rect(screen, Colors.BG_CARD, sc_rect, border_radius=4)
                pygame.draw.rect(screen, Colors.BORDER_DEFAULT, sc_rect, width=1, border_radius=4)

                if show_spells:
                    sign = "+" if spell.charge > 0 else ""
                    charge_text = f"[{sign}{spell.charge}]"
                    charge_color = Colors.CATION_PRIMARY if spell.charge > 0 else Colors.ANION_PRIMARY
                else:
                    charge_text = "[?]"
                    charge_color = Colors.HIDDEN_MYSTERY

                name_surf = self.desc_font.render(f"{spell.ion.name} ({spell.ion.formula})", True, Colors.TEXT_HIGH)
                chg_surf = self.text_font.render(charge_text, True, charge_color)

                screen.blit(name_surf, (sc_rect.x + 10, sc_rect.y + (sc_rect.h - name_surf.get_height()) // 2))
                screen.blit(chg_surf, (sc_rect.right - 10 - chg_surf.get_width(),
                                       sc_rect.y + (sc_rect.h - chg_surf.get_height()) // 2))

    def _draw_chest_modal(self, screen: pygame.Surface) -> None:
        self._draw_dim_overlay(screen)

        modal_rect = pygame.Rect(self.modal_x, self.modal_y, self.modal_w, self.modal_h)
        pygame.draw.rect(screen, Colors.BG_CARD, modal_rect, border_radius=8)
        pygame.draw.rect(screen, Colors.HIDDEN_MYSTERY, modal_rect, width=3, border_radius=8)

        # Text placements are relative to modal bounds
        hdr = self.header_font.render("CHEST CLAIMED!", True, Colors.HIDDEN_MYSTERY)
        screen.blit(hdr,
                    (modal_rect.x + (modal_rect.w - hdr.get_width()) // 2, modal_rect.y + int(self.modal_h * 0.12)))

        txt1 = self.desc_font.render("Inside, you discover a new spell:", True, Colors.TEXT_HIGH)
        screen.blit(txt1,
                    (modal_rect.x + (modal_rect.w - txt1.get_width()) // 2, modal_rect.y + int(self.modal_h * 0.35)))

        if self.gained_spell:
            sign = "+" if self.gained_spell.charge > 0 else ""
            show_spells = self.engine.config.visibility.name.lower() in {"both", "spells_only"}
            chg_val = f"[{sign}{self.gained_spell.charge}]" if show_spells else "[?]"

            spell_txt = f"{self.gained_spell.ion.name.upper()} {chg_val}"
            color = Colors.CATION_PRIMARY if self.gained_spell.charge > 0 else Colors.ANION_PRIMARY
            spell_surf = self.text_font.render(spell_txt, True, color)
            screen.blit(spell_surf, (modal_rect.x + (modal_rect.w - spell_surf.get_width()) // 2,
                                     modal_rect.y + int(self.modal_h * 0.5)))

        if self.chest_dismiss_btn:
            self.chest_dismiss_btn.draw(screen)

    def _draw_exit_modal(self, screen: pygame.Surface) -> None:
        self._draw_dim_overlay(screen)

        modal_rect = pygame.Rect(self.modal_x, self.modal_y, self.modal_w, self.modal_h)
        pygame.draw.rect(screen, Colors.BG_CARD, modal_rect, border_radius=8)
        pygame.draw.rect(screen, Colors.ROOM_EXIT, modal_rect, width=3, border_radius=8)

        hdr = self.header_font.render("DUNGEON EXIT", True, Colors.ROOM_EXIT)
        screen.blit(hdr,
                    (modal_rect.x + (modal_rect.w - hdr.get_width()) // 2, modal_rect.y + int(self.modal_h * 0.12)))

        txt1 = self.desc_font.render("Do you want to escape and", True, Colors.TEXT_HIGH)
        txt2 = self.desc_font.render("complete your run?", True, Colors.TEXT_HIGH)
        screen.blit(txt1,
                    (modal_rect.x + (modal_rect.w - txt1.get_width()) // 2, modal_rect.y + int(self.modal_h * 0.35)))
        screen.blit(txt2,
                    (modal_rect.x + (modal_rect.w - txt2.get_width()) // 2, modal_rect.y + int(self.modal_h * 0.46)))

        if self.exit_yes_btn and self.exit_no_btn:
            self.exit_yes_btn.draw(screen)
            self.exit_no_btn.draw(screen)

    def _draw_dim_overlay(self, screen: pygame.Surface) -> None:
        # Fills only the map viewport area
        dim = pygame.Surface((self.map_area_width - (2 * self.padding), self.screen_height - (2 * self.padding)),
                             pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        screen.blit(dim, (self.padding, self.padding))

    def _get_grid_coord_from_pixels(self, pos: tuple[int, int]) -> tuple[int, int] | None:
        px, py = pos
        mx = px - self.grid_offset_x
        my = py - self.grid_offset_y

        col = mx // (self.tile_size + self.tile_spacing)
        row = my // (self.tile_size + self.tile_spacing)

        if 0 <= col < self.dungeon.width and 0 <= row < self.dungeon.height:
            rx = col * (self.tile_size + self.tile_spacing)
            ry = row * (self.tile_size + self.tile_spacing)
            if rx <= mx < rx + self.tile_size and ry <= my < ry + self.tile_size:
                return col, row
        return None

    def _complete_run(self) -> None:
        pass
        #from game.gui.views.summary_scene import SummaryScene
        #self.manager.change_scene(SummaryScene(self.manager, self.engine))
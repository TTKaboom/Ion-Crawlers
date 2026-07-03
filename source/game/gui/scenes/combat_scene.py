from __future__ import annotations

import pygame
from game.combat import CastResult
from game.engine import GameEngine
from game.gui.scene import Scene, SceneManager
from game.gui.colors import Colors
from game.gui.ui import Button


class CombatScene(Scene):
    def __init__(self, manager: SceneManager, engine: GameEngine, previous_position: tuple[int, int],
                 screen_width: int, screen_height: int):
        super().__init__(manager)
        self.engine = engine
        self.previous_position = previous_position
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.header_font = pygame.font.SysFont("Arial", 24, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 20)
        self.desc_font = pygame.font.SysFont("Arial", 16)

        self.encounter = engine.start_encounter()
        self.selected_spell_index: int | None = None
        self.last_result: CastResult | None = None
        self.state = "SELECTING"

        self.padding = 20
        self._init_layout()

        self.cast_button = Button(
            self.spellbook_x, self.spellbook_y + self.spellbook_h - 50,
            120, 40, "CAST", self.text_font, Colors.NEUTRAL_DARK)
        self.flee_button = Button(
            self.spellbook_x + 140, self.spellbook_y + self.spellbook_h - 50,
            120, 40, "FLEE", self.text_font, Colors.CATION_DARK)
        self.continue_button = Button(
            self.screen_width // 2 - 80, self.log_y + self.log_h - 50,
            160, 40, "CONTINUE", self.desc_font, Colors.NEUTRAL_DARK)
        self.return_button = Button(
            self.screen_width // 2 - 110, self.screen_height - 90,
            220, 50, "RETURN TO DUNGEON", self.text_font, Colors.NEUTRAL_DARK)

        self.spell_cards: list[dict] = []
        self._build_spell_cards()

    def _init_layout(self):
        p = self.padding
        sw = self.screen_width
        sh = self.screen_height

        self.monster_x = p
        self.monster_y = p
        self.monster_w = int(sw * 0.55) - p * 2
        self.monster_h = int(sh * 0.28)

        self.hud_x = int(sw * 0.55) + p
        self.hud_y = p
        self.hud_w = sw - self.hud_x - p
        self.hud_h = self.monster_h

        self.log_x = p
        self.log_y = self.monster_y + self.monster_h + p
        self.log_w = sw - p * 2
        self.log_h = int(sh * 0.18)

        self.spellbook_x = p
        self.spellbook_y = self.log_y + self.log_h + p
        self.spellbook_w = sw - p * 2
        self.spellbook_h = sh - self.spellbook_y - p

    def _build_spell_cards(self):
        self.spell_cards.clear()
        self.selected_spell_index = None
        player = self.engine.state.player

        card_w = 90
        card_h = 64
        gap = 8
        available = [(i, s) for i, s in enumerate(player.spells) if not s.used]
        if not available:
            self.state = "NO_SPELLS"
            return

        total_w = len(available) * (card_w + gap) - gap
        start_x = self.spellbook_x + (self.spellbook_w - total_w) // 2
        y = self.spellbook_y + 35

        for idx, (full_idx, spell) in enumerate(available):
            x = start_x + idx * (card_w + gap)
            rect = pygame.Rect(x, y, card_w, card_h)
            self.spell_cards.append({
                "full_index": full_idx,
                "rect": rect,
                "spell": spell,
            })

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.state == "SELECTING":
            self._handle_selecting_event(event)
        elif self.state == "RESULT":
            self._handle_result_event(event)
        elif self.state in ("VICTORY", "DEFEATED", "NO_SPELLS"):
            self._handle_terminal_event(event)

    def _handle_selecting_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for card in self.spell_cards:
                if card["rect"].collidepoint(pos):
                    self.selected_spell_index = card["full_index"]
            if self.cast_button.rect.collidepoint(pos) and self.selected_spell_index is not None:
                self._cast_spell()
            if self.flee_button.rect.collidepoint(pos):
                self._flee()

    def _handle_result_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.continue_button.rect.collidepoint(event.pos):
                self._advance_after_result()
        elif event.type == pygame.KEYDOWN and event.key in {pygame.K_SPACE, pygame.K_RETURN}:
            self._advance_after_result()

    def _advance_after_result(self):
        player = self.engine.state.player
        if self.last_result and self.last_result.defeated:
            self.state = "VICTORY"
        elif not player.is_alive():
            self.state = "DEFEATED"
        elif not player.available_spells():
            self.state = "NO_SPELLS"
        else:
            self.state = "SELECTING"
            self._build_spell_cards()

    def _handle_terminal_event(self, event: pygame.event.Event) -> None:
        if self.state == "DEFEATED":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.return_button.rect.collidepoint(event.pos):
                    from game.gui.scenes.title_scene import TitleScene
                    self.manager.change_scene(TitleScene(self.manager))
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.return_button.rect.collidepoint(event.pos):
                self._end_combat()
        elif event.type == pygame.KEYDOWN and event.key in {pygame.K_SPACE, pygame.K_RETURN}:
            self._end_combat()

    def _cast_spell(self):
        if self.selected_spell_index is None:
            return
        self.last_result = self.engine.cast_spell(self.encounter, self.selected_spell_index)
        self.state = "RESULT"

    def _flee(self):
        self.engine.state.player.position = self.previous_position
        self._end_combat()

    def _end_combat(self):
        from game.gui.scenes.dungeon_scene import DungeonScene
        if self.engine.is_run_over():
            self.engine.finalize_score()
        self.manager.change_scene(
            DungeonScene(self.manager, self.engine, self.screen_height, self.screen_width))

    def update(self, dt: float) -> None:
        mouse_pos = pygame.mouse.get_pos()
        if self.state == "SELECTING":
            self.cast_button.check_hover(mouse_pos)
            self.flee_button.check_hover(mouse_pos)
        elif self.state == "RESULT":
            self.continue_button.check_hover(mouse_pos)
        elif self.state in ("VICTORY", "NO_SPELLS", "DEFEATED"):
            self.return_button.check_hover(mouse_pos)

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(Colors.BG_DARK)
        self._draw_monster_panel(screen)
        self._draw_player_hud(screen)
        self._draw_battle_log(screen)
        self._draw_spellbook(screen)

    def _draw_monster_panel(self, screen: pygame.Surface) -> None:
        rect = pygame.Rect(self.monster_x, self.monster_y, self.monster_w, self.monster_h)
        pygame.draw.rect(screen, Colors.BG_CARD, rect, border_radius=8)
        pygame.draw.rect(screen, Colors.ROOM_MONSTER, rect, width=2, border_radius=8)

        monster = self.encounter.monster
        y = self.monster_y + 15

        title = self.header_font.render("MONSTER", True, Colors.ROOM_MONSTER)
        screen.blit(title, (self.monster_x + 15, y))
        y += 30

        name = self.text_font.render(monster.name, True, Colors.TEXT_HIGH)
        screen.blit(name, (self.monster_x + 15, y))
        y += 28

        for ion in monster.ions:
            sign = "+" if ion.charge > 0 else ""
            txt = self.desc_font.render(f"{ion.formula} [{sign}{ion.charge}]", True, Colors.TEXT_MUTED)
            screen.blit(txt, (self.monster_x + 15, y))
            y += 20

        y += 8
        net = self.desc_font.render(f"Net Charge: {monster.net_charge:+d}", True, Colors.TEXT_HIGH)
        screen.blit(net, (self.monster_x + 15, y))
        y += 24

        bar_w = self.monster_w - 30
        bar_h = 20
        bar_x = self.monster_x + 15
        bar_y = y
        pygame.draw.rect(screen, Colors.BORDER_DEFAULT, (bar_x, bar_y, bar_w, bar_h), border_radius=4)

        init = self.encounter.initial_charge
        if init != 0:
            pct = max(0.0, min(1.0, abs(self.encounter.remaining_charge) / abs(init)))
            fill_w = int((bar_w - 4) * pct)
            if fill_w > 0:
                fill_color = Colors.ROOM_MONSTER if pct > 0.4 else Colors.CATION_PRIMARY
                pygame.draw.rect(screen, fill_color, (bar_x + 2, bar_y + 2, fill_w, bar_h - 4), border_radius=2)

        rem = self.desc_font.render(f"Remaining: {self.encounter.remaining_charge:+d}", True, Colors.TEXT_HIGH)
        screen.blit(rem, (bar_x + bar_w - rem.get_width() - 5, bar_y + (bar_h - rem.get_height()) // 2))

    def _draw_player_hud(self, screen: pygame.Surface) -> None:
        rect = pygame.Rect(self.hud_x, self.hud_y, self.hud_w, self.hud_h)
        pygame.draw.rect(screen, Colors.BG_CARD, rect, border_radius=8)
        pygame.draw.rect(screen, Colors.BORDER_DEFAULT, rect, width=2, border_radius=8)

        player = self.engine.state.player
        y = self.hud_y + 15

        title = self.header_font.render("PLAYER", True, Colors.TEXT_HIGH)
        screen.blit(title, (self.hud_x + 15, y))
        y += 30

        hp_label = self.desc_font.render("Health:", True, Colors.TEXT_MUTED)
        screen.blit(hp_label, (self.hud_x + 15, y))
        y += 20

        bar_w = self.hud_w - 30
        bar_h = 18
        bar_x = self.hud_x + 15
        pygame.draw.rect(screen, Colors.BORDER_DEFAULT, (bar_x, y, bar_w, bar_h), border_radius=4)

        max_hp = self.engine.config.difficulty.starting_health
        pct = max(0.0, min(1.0, player.health / max_hp))
        fill_w = int((bar_w - 4) * pct)
        if fill_w > 0:
            fill_color = Colors.NEUTRAL_SUCCESS if pct > 0.4 else Colors.CATION_PRIMARY
            pygame.draw.rect(screen, fill_color, (bar_x + 2, y + 2, fill_w, bar_h - 4), border_radius=2)

        hp_text = self.desc_font.render(f"{player.health} / {max_hp}", True, Colors.TEXT_HIGH)
        screen.blit(hp_text, (bar_x + bar_w - hp_text.get_width() - 5, y + (bar_h - hp_text.get_height()) // 2))
        y += bar_h + 15

        score = self.text_font.render(f"Score Base: {player.total_charge_offset}", True, Colors.TEXT_MUTED)
        screen.blit(score, (self.hud_x + 15, y))
        y += 25

        defeated = self.desc_font.render(f"Defeated: {player.monsters_defeated}", True, Colors.TEXT_MUTED)
        screen.blit(defeated, (self.hud_x + 15, y))

    def _draw_battle_log(self, screen: pygame.Surface) -> None:
        rect = pygame.Rect(self.log_x, self.log_y, self.log_w, self.log_h)
        pygame.draw.rect(screen, Colors.BG_CARD, rect, border_radius=8)
        pygame.draw.rect(screen, Colors.BORDER_DEFAULT, rect, width=1, border_radius=8)

        label = self.desc_font.render("BATTLE LOG", True, Colors.TEXT_MUTED)
        screen.blit(label, (self.log_x + 15, self.log_y + 10))

        if self.state == "RESULT" and self.last_result:
            if self.last_result.damage > 0:
                msg_color = Colors.DAMAGE_FLASH
            elif self.last_result.defeated:
                msg_color = Colors.NEUTRAL_SUCCESS
            else:
                msg_color = Colors.TEXT_HIGH
            msg = self.text_font.render(self.last_result.message, True, msg_color)
            screen.blit(msg, (self.log_x + 15, self.log_y + 40))

            if self.last_result.damage > 0:
                dmg = self.desc_font.render(f"Damage taken: {self.last_result.damage}", True, Colors.DAMAGE_FLASH)
                screen.blit(dmg, (self.log_x + 15, self.log_y + 65))

            self.continue_button.draw(screen)

        if self.state == "VICTORY":
            victory = self.text_font.render("Monster defeated!", True, Colors.NEUTRAL_SUCCESS)
            screen.blit(victory, (self.log_x + 15, self.log_y + 40))
            if self.last_result and self.last_result.damage > 0:
                dmg = self.desc_font.render(f"Overcharge damage taken: {self.last_result.damage}", True,
                                            Colors.DAMAGE_FLASH)
                screen.blit(dmg, (self.log_x + 15, self.log_y + 65))

        if self.state == "DEFEATED":
            defeat = self.text_font.render("You have been defeated!", True, Colors.DAMAGE_FLASH)
            screen.blit(defeat, (self.log_x + 15, self.log_y + 40))

    def _draw_spellbook(self, screen: pygame.Surface) -> None:
        rect = pygame.Rect(self.spellbook_x, self.spellbook_y, self.spellbook_w, self.spellbook_h)
        pygame.draw.rect(screen, Colors.BG_CARD, rect, border_radius=8)
        pygame.draw.rect(screen, Colors.BORDER_DEFAULT, rect, width=1, border_radius=8)

        label = self.header_font.render("SPELLBOOK", True, Colors.TEXT_MUTED)
        screen.blit(label, (self.spellbook_x + 15, self.spellbook_y + 10))

        if self.state == "NO_SPELLS":
            msg = self.text_font.render("No spells remaining!", True, Colors.CATION_PRIMARY)
            screen.blit(msg, (self.spellbook_x + 15, self.spellbook_y + 55))
            self.return_button.draw(screen)
            return

        show_charges = self.engine.config.visibility.name.lower() in {"both", "spells_only"}
        for card in self.spell_cards:
            spell = card["spell"]
            r = card["rect"]
            selected = card["full_index"] == self.selected_spell_index

            border = Colors.BORDER_ACTIVE if selected else Colors.BORDER_DEFAULT
            pygame.draw.rect(screen, Colors.BG_DARK, r, border_radius=6)
            pygame.draw.rect(screen, border, r, width=2 if selected else 1, border_radius=6)

            name_surf = self.desc_font.render(spell.ion.name, True, Colors.TEXT_HIGH)
            screen.blit(name_surf, (r.x + (r.w - name_surf.get_width()) // 2, r.y + 6))

            formula_surf = self.desc_font.render(spell.ion.formula, True, Colors.TEXT_MUTED)
            screen.blit(formula_surf, (r.x + (r.w - formula_surf.get_width()) // 2, r.y + 26))

            if show_charges:
                sign = "+" if spell.charge > 0 else ""
                charge_color = Colors.CATION_PRIMARY if spell.charge > 0 else Colors.ANION_PRIMARY
                charge_surf = self.desc_font.render(f"[{sign}{spell.charge}]", True, charge_color)
            else:
                charge_surf = self.desc_font.render("[?]", True, Colors.HIDDEN_MYSTERY)
            screen.blit(charge_surf, (r.x + (r.w - charge_surf.get_width()) // 2, r.y + 44))

        if self.state == "SELECTING":
            self.cast_button.draw(screen)
            self.flee_button.draw(screen)
        elif self.state == "VICTORY":
            self.return_button.draw(screen)
        elif self.state == "DEFEATED":
            self.return_button.draw(screen)

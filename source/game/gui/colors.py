"""Chemical-themed color palette constants for Ion Crawler GUI."""

from typing import NamedTuple

class ColorRGB(NamedTuple):
    r: int
    g: int
    b: int

class Colors:
    # 1. Base UI Palette (Futuristic Dark Sci-Fi / Dungeon crawl theme)
    BG_DARK = ColorRGB(18, 18, 24)         # Deep space dark-blue background
    BG_CARD = ColorRGB(28, 28, 38)         # Slightly lighter slate-blue for cards/panels
    BORDER_DEFAULT = ColorRGB(60, 60, 75)  # Muted gray-blue for resting outlines
    BORDER_ACTIVE = ColorRGB(33, 150, 243)  # Vibrant neon cyan for active focuses/hover highlights

    # 2. Text Palette
    TEXT_HIGH = ColorRGB(240, 240, 250)    # Crisp off-white for primary readability
    TEXT_MUTED = ColorRGB(150, 150, 170)   # Medium slate-gray for headers and help text
    TEXT_DISABLED = ColorRGB(90, 90, 100)   # Muted ash-gray for spent spells or locked options

    # 3. Chemistry Theme Palette
    # Cations (+) -> Warm, reactive, acidic coral-red
    CATION_PRIMARY = ColorRGB(239, 83, 80) # Vibrant coral red
    CATION_DARK = ColorRGB(198, 40, 40)    # Deep crimson red

    # Anions (-) -> Cool, electric, basic cyan-blue
    ANION_PRIMARY = ColorRGB(41, 182, 246) # Electric sky blue
    ANION_DARK = ColorRGB(21, 101, 192)    # Deep cobalt blue

    # Neutralized / Stable state -> Calm, stable green
    NEUTRAL_SUCCESS = ColorRGB(76, 175, 80) # Bright leaf green
    NEUTRAL_DARK = ColorRGB(46, 125, 50)    # Soft emerald green

    # Hidden / Mystery / Unidentified -> Golden Amber
    HIDDEN_MYSTERY = ColorRGB(255, 179, 0)  # Warm amber gold
    HIDDEN_DARK = ColorRGB(255, 143, 0)     # Burnt orange

    # 4. Map Grid & Room States
    ROOM_FOG = ColorRGB(35, 35, 40)          # Unvisited room (unrevealed fog-of-war)
    ROOM_EMPTY = ColorRGB(55, 55, 65)        # Visited empty room (safe grey slate)
    ROOM_START = ColorRGB(46, 125, 50)       # Start room (safe forest green)
    ROOM_EXIT = ColorRGB(106, 27, 154)       # Exit room (mystical amethyst purple)
    ROOM_CHEST = ColorRGB(230, 81, 0)        # Treasure room (chest gold)
    ROOM_MONSTER = ColorRGB(183, 28, 28)     # Hostile monster room (danger red)
    PLAYER_MARKER = ColorRGB(33, 150, 243)   # Neon blue dot representing player position

    # 5. Visual Special Effects
    DAMAGE_FLASH = ColorRGB(211, 47, 47)     # Crimson flash overlay on player screen shake
    HEAL_GLOW = ColorRGB(129, 199, 132)      # Soft lime glow for spellbook reward claim
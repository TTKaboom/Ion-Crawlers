# Ion Crawler

## Overview

Ion Crawler is a dungeon crawler-style game where the monsters are cations or anions and must be defeated by the player casting one or more ion spells where the ions they use have to negate the total charge to defeat the monster.

## Game Modes

The game supports three modes:

- Anion (monsters are anions and the player will have a set of cation spells that can be used to offset the monsters)
- Cation (inverse of above - the player has anion spells and monsters are cations)
- Mixed (same as above but the monsters are cation & anion and the player has spells from both)

## Logic

The ionic charge of the monsters should match the ionic charge of the spells that the player has. There will be a set of all the potentinal ions and ionic molecules that can appear in the game but each round will only have a subset of these.

The round will end when the player has used all of their spells, or the player has defeated all of the monsters. Points will be awarded based on the percentage of monster charge that the player successfully offsets.

Monsters can be made up of multiple anions, multiple cations, or both anions and cations that will offset and mean the player only needs a smaller ionic spell or set of spells.

## Presentation

The game will be a pixel art style where the monster is presented face-on to the player.

A maze-like dungeon environment should be created where the user can explore the dungeon by moving from room to room. Monster encounters will show a fight screen where the user will be able to see the ion(s) for the monster and can select the ion spells they wish to use.

As the player moves around the dungeon they may encounter treasure chests that will give them additional ionic spells.

## Combat Math Examples

If the monster is ammonium (+1 charge) the following rules apply:
- if player casts -1 then the monster is defeated.
- if player casts -2 then the monster is defeated but the player takes 1 damage because they used additional charge.
- if player casts +1 then the monster is still alive and the player take 1 damage.
- if player casts +2 then the monster is still alive and the player takes 2 damnage.

There should be different difficultly levels that give the user different amounts of health. When a user has sustained total damage equal to or greater than their health they have died and the game is over.

## Data

The supported ions and molecules should be defined in a csv file that looks like this:

```
Name, Formula, Charge, Type
ammonium, NH4, +1, standard
caesium, Cs, +1, standard
copper(1), Cu, +1, standard
bromide, Br, -1, standard
ehanoate/acetate, CH3COO, -1, standard
pyrophosphate, P2O4, -4, extended
```

## Tech Stack

The game should be programmed in Python and should use full object-oriented design.



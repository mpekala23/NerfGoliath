import arcade
from arcade import key as KEY
import game.consts as consts
import time
import math
from schema import Spell

EXPLODE_FOR = 240  # In milliseconds

SPELL_SCALING = 1.5
EXPLODE_SCALING = 2


class SpellSprite(arcade.Sprite):
    def __init__(self, state: Spell):
        super().__init__("game/assets/images/explosion_f0.png", SPELL_SCALING)

        self.state = state
        self.scale = SPELL_SCALING

    @staticmethod
    def get_new_state(old_state: Spell):
        return Spell(
            old_state.id,
            old_state.pos + old_state.vel,
            old_state.vel,
            old_state.creator,
        )

    def on_update(self, delta_time: float = 1 / 60):
        self.center_x, self.center_y = self.state.pos.x, self.state.pos.y
        self.state.pos += self.state.vel
        self.change_x, self.change_y = (0, 0)

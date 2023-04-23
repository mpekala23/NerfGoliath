import arcade
from arcade import key as KEY
from utils import Vec2
import consts
import time

LIVE_FOR = 500  # In milliseconds
EXPLODE_FOR = 150  # In milliseconds

SPELL_SCALING = 0.25
EXPLODE_SCALING = 2


class Spell(arcade.Sprite):
    def __init__(self, pos: Vec2, vel: Vec2, parent):
        super().__init__("assets/images/spell_anim_f0.png", SPELL_SCALING)
        self.center_x = pos.x
        self.center_y = pos.y
        self.change_x = vel.x
        self.change_y = vel.y
        self.born_at = time.time()
        self.exploding = False
        self.exploded_at = time.time()
        self.parent = parent

    def explode(self):
        self.exploded_at = time.time()
        self.exploding = True
        self.change_x /= 10
        self.change_y /= 10

    def on_update(self, delta_time: float = 1 / 60):
        if self.exploding:
            diff = time.time() - self.exploded_at
            ratio = diff * 1000.0 / EXPLODE_FOR
            self.scale = SPELL_SCALING + (EXPLODE_SCALING - SPELL_SCALING) * ratio
            if time.time() - self.exploded_at > EXPLODE_FOR / 1000.0:
                self.kill()
        else:
            if time.time() - self.born_at > LIVE_FOR / 1000.0:
                self.explode()

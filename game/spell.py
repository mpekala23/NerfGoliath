import arcade
from arcade import key as KEY
from utils import Vec2
import consts
import time
import math
from arcade.experimental import Shadertoy

EXPLODE_FOR = 240  # In milliseconds

SPELL_SCALING = 1.5
EXPLODE_SCALING = 2


class Spell(arcade.Sprite):
    def __init__(self, pos: Vec2, vel: Vec2, parent):
        super().__init__("assets/images/explosion_f0.png", SPELL_SCALING)

        self.vel = vel
        self.center_x = pos.x
        self.center_y = pos.y
        self.change_x = vel.x
        self.change_y = vel.y
        self.born_at = time.time()
        self.exploding = False
        self.exploded_at = time.time()
        self.parent = parent
        self.scale = SPELL_SCALING

        self.cur_frame = 0
        self.explode_textures = []
        for i in range(4):
            self.explode_textures.append(
                arcade.load_texture(
                    f"assets/images/explosion_f{i}.png",
                )
            )
        self.texture = self.explode_textures[0]
        self.cur_texture = 0
        self.update_hit_box()

        shader_file_path = "shaders/spell.glsl"
        window_size = (consts.SCREEN_WIDTH, consts.SCREEN_HEIGHT)
        self.shadertoy = Shadertoy.create_from_file(window_size, shader_file_path)

    def update_hit_box(self):
        val = 36 if self.exploding else 8
        self.set_hit_box([(-val, -val), (-val, val), (val, val), (val, -val)])

    def explode(self):
        self.exploded_at = time.time()
        self.exploding = True
        self.texture = self.explode_textures[0]
        self.update_hit_box()
        self.scale = EXPLODE_SCALING

    def on_update(self, delta_time: float = 1 / 60):
        if self.exploding:
            diff = time.time() - self.exploded_at
            ratio = diff * 1000.0 / EXPLODE_FOR
            cur_frame = min(3, math.floor(ratio * 4))
            self.texture = self.explode_textures[cur_frame]
            if time.time() - self.exploded_at > EXPLODE_FOR / 1000.0:
                self.kill()
        else:
            diff = time.time() - self.born_at
            ratio = min(diff * 1000.0 / consts.SPELL_LIVE_FOR, 1)
            if ratio >= 1:
                self.explode()
            self.change_x = self.vel.x * math.cos(math.pi * 0.5 * ratio)
            self.change_y = self.vel.y * math.cos(math.pi * 0.5 * ratio)
            anim_speed = 0.1
            self.cur_texture += 1
            cur_frame = int(self.cur_texture * anim_speed) % 2
            self.texture = self.explode_textures[cur_frame]

    def on_draw(self):
        self.shadertoy.program["pos"] = self.center_x * 2, self.center_y * 2
        self.shadertoy.render()

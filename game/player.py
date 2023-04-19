import arcade
from arcade import key as KEY
import consts
import math


class Player(arcade.Sprite):
    def __init__(self):
        super().__init__(
            "assets/images/wizzard_m_idle_anim_f0.png", consts.WIZARD_SCALING
        )
        self.facing = consts.RIGHT
        self.center_x = 100
        self.center_y = 100
        self.press_map = {"left": False, "right": False, "up": False, "down": False}
        self.scale = consts.WIZARD_SCALING

        self.cur_texture = 0
        self.run_textures = {
            consts.RIGHT: [],
            consts.LEFT: [],
        }
        for i in range(4):
            right_texture = arcade.load_texture(
                f"assets/images/wizzard_m_run_anim_f{i}.png",
            )
            left_texture = arcade.load_texture(
                f"assets/images/wizzard_m_run_anim_f{i}.png",
                flipped_horizontally=True,
            )
            self.run_textures[consts.RIGHT].append(right_texture)
            self.run_textures[consts.LEFT].append(left_texture)
        self.idle_textures = {
            consts.RIGHT: [],
            consts.LEFT: [],
        }
        for i in range(4):
            right_texture = arcade.load_texture(
                f"assets/images/wizzard_m_idle_anim_f{i}.png",
            )
            left_texture = arcade.load_texture(
                f"assets/images/wizzard_m_idle_anim_f{i}.png",
                flipped_horizontally=True,
            )
            self.idle_textures[consts.RIGHT].append(right_texture)
            self.idle_textures[consts.LEFT].append(left_texture)

    def setup(self):
        pass

    def update_animation(self, delta_time: float = 1 / 60):
        anim_speed = 0.1
        self.cur_texture += 1
        cur_frame = int(self.cur_texture * anim_speed) % 4

        if self.change_x < 0 and self.facing == consts.RIGHT:
            self.facing = consts.LEFT
        elif self.change_x > 0 and self.facing == consts.LEFT:
            self.facing = consts.RIGHT

        if self.change_x != 0 or self.change_y != 0:
            # Player is moving
            self.texture = self.run_textures[self.facing][cur_frame]
        else:
            # Player is idle
            self.texture = self.idle_textures[self.facing][cur_frame]

    def update_press_map(self, press_map):
        self.press_map = press_map

    def frame(self, delta_time):
        PLAYER_SPEED = 4
        self.change_x = 0
        self.change_y = 0
        if self.press_map["left"] and not self.press_map["right"]:
            self.change_x = -PLAYER_SPEED
        if not self.press_map["left"] and self.press_map["right"]:
            self.change_x = PLAYER_SPEED
        if self.press_map["up"] and not self.press_map["down"]:
            self.change_y = PLAYER_SPEED
        if not self.press_map["up"] and self.press_map["down"]:
            self.change_y = -PLAYER_SPEED
        total_speed = math.sqrt(self.change_x**2 + self.change_y**2)
        if total_speed > 0:
            self.change_x /= total_speed
            self.change_y /= total_speed
            self.change_x *= PLAYER_SPEED
            self.change_y *= PLAYER_SPEED
        self.update_animation()

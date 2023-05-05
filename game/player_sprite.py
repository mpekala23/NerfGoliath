import sys

sys.path.append("..")

import arcade
from game.consts import (
    RIGHT,
    LEFT,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    DAVID_SCALING,
    GOLIATH_SCALING,
)
from schema import Player, Vec2, KeyInput, MouseInput, InputState

PLAYER_SPEED = 6
CAST_SPEED = 3
DASH_SPEED = 18
DASH_LENGTH = 150  # In milliseconds
DASH_COOLDOWN = 600  # In milliseconds


class PlayerSprite(arcade.Sprite):
    def __init__(self, name: str, is_you: bool):
        super().__init__("game/assets/images/them0.png", GOLIATH_SCALING)
        person = "you" if is_you else "them"
        self.cur_texture = 0
        self.run_textures = {
            RIGHT: [],
            LEFT: [],
        }
        for i in range(4):
            right_texture = arcade.load_texture(
                f"game/assets/images/{person}_run{i}.png",
            )
            left_texture = arcade.load_texture(
                f"game/assets/images/{person}_run{i}.png",
                flipped_horizontally=True,
            )
            self.run_textures[RIGHT].append(right_texture)
            self.run_textures[LEFT].append(left_texture)
        self.idle_textures = {
            RIGHT: [],
            LEFT: [],
        }
        for i in range(4):
            right_texture = arcade.load_texture(
                f"game/assets/images/{person}_run{i // 2}.png",
            )
            left_texture = arcade.load_texture(
                f"game/assets/images/{person}_run{i // 2}.png",
                flipped_horizontally=True,
            )
            self.idle_textures[RIGHT].append(right_texture)
            self.idle_textures[LEFT].append(left_texture)
        self.death_textures = {RIGHT: [], LEFT: []}
        for i in range(4):
            right_texture = arcade.load_texture(
                f"game/assets/images/wizzard_m_death_f{i}.png",
            )
            left_texture = arcade.load_texture(
                f"game/assets/images/wizzard_m_death_f{i}.png",
                flipped_horizontally=True,
            )
            self.death_textures[RIGHT].append(right_texture)
            self.death_textures[LEFT].append(left_texture)

        self.state = Player(name, Vec2(0, 0), Vec2(0, 0))
        self.scale = GOLIATH_SCALING

    def is_dead(self):
        return self.state.time_till_respawn > 0

    def kill(self):
        self.cur_texture = 0

    def update_animation(self, delta_time: float = 1 / 60):
        self.scale = DAVID_SCALING if self.state.is_david else GOLIATH_SCALING
        anim_speed = 0.1
        self.cur_texture += 1
        cur_frame = int(float(self.cur_texture * anim_speed)) % 4

        if self.state.vel.x != 0 or self.state.vel.y != 0:
            # Player is moving
            self.texture = self.run_textures[self.state.facing][cur_frame]
        else:
            # Player is idle
            self.texture = self.idle_textures[self.state.facing][cur_frame]

        if self.is_dead():
            # if int(self.cur_texture * anim_speed) >= 4:
            #     self.scale = 0
            self.texture = self.death_textures[self.state.facing][cur_frame]
            self.center_x, self.center_y = -1000, -1000

    def on_update(self, delta_time):
        """ """
        self.center_x, self.center_y = self.state.pos.x, self.state.pos.y
        self.change_x, self.change_y = (0, 0)
        self.state.pos += self.state.vel
        self.update_animation()

    @staticmethod
    def get_player_movement_from_inp(
        key_input: KeyInput, mouse_input: MouseInput
    ) -> Vec2:
        x = 0
        y = 0
        if key_input.right and not key_input.left:
            x = 1
        if key_input.left and not key_input.right:
            x = -1
        if key_input.up and not key_input.down:
            y = 1
        if key_input.down and not key_input.up:
            y = -1
        result = Vec2(x, y)
        result.normalize()
        actual_speed = CAST_SPEED if mouse_input.right else PLAYER_SPEED
        result *= actual_speed
        return result

    @staticmethod
    def get_new_state(old_state: Player, p_inp: InputState) -> Player:
        new_vel = PlayerSprite.get_player_movement_from_inp(
            p_inp.key_input, p_inp.mouse_input
        )
        new_pos = old_state.pos
        new_pos.x = min(SCREEN_WIDTH, max(0, new_pos.x))
        new_pos.y = min(SCREEN_HEIGHT, max(0, new_pos.y))
        new_is_alive = old_state.is_alive
        new_time_till_respawn = old_state.time_till_respawn
        new_casting = p_inp.mouse_input.right
        new_facing = old_state.facing
        if new_casting:
            new_facing = LEFT if p_inp.mouse_input.pos.x < new_pos.x else RIGHT
        elif new_vel.x != 0:
            new_facing = LEFT if new_vel.x < 0 else RIGHT
        return Player(
            old_state.id,
            new_pos,
            new_vel,
            new_is_alive,
            new_time_till_respawn,
            new_facing,
            new_casting,
            score=old_state.score,
        )

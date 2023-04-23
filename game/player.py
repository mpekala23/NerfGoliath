from typing import Union
import arcade
from arcade import MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT
import consts
import math
import time
from utils import Mouse, KeyInput, Vec2

WIZARD_SCALING = 3
PLAYER_SPEED = 6
CAST_SPEED = 3
DASH_SPEED = 18
DASH_LENGTH = 150  # In milliseconds
DASH_COOLDOWN = 600  # In milliseconds


class PlayerState:
    """
    This contains all of the state that determines how a player (self or enemy)
    should render. For players connected over the wire, abstracting this out
    lets us simply directly update the state from the network controller to
    mimic their movements for other players. (Also for AI.)
    """

    def __init__(
        self,
        x: float,
        y: float,
        dx: float,
        dy: float,
        casting: bool = False,
        dashing: bool = False,
    ):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.casting = casting
        self.dashing = dashing

    def __str__(self):
        return f"pos: ({self.x}, {self.y}), vel: ({self.dx}, {self.dy}), casting: {self.casting}"


class Player(arcade.Sprite):
    def __init__(self, is_managed: bool):
        # Keep track of whether this should respond to keyboard inputs
        self.is_managed = is_managed
        # Load the textures
        super().__init__("assets/images/wizzard_m_idle_anim_f0.png", WIZARD_SCALING)
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

        # Set the state and dirty details
        self.state = PlayerState(x=100, y=100, dx=0, dy=0, casting=False, dashing=False)
        self.center_x = self.state.x
        self.center_y = self.state.y
        self.change_x = self.state.dx
        self.change_y = self.state.dy
        self.died_at: Union[None, float] = None
        self.dash_start: float = time.time()

        # State variables that are functions of the above state
        self.facing = consts.RIGHT
        self.scale = WIZARD_SCALING

        # Setup for inputs (will only be used if this is "actually" the player)
        self.press_map = KeyInput(False, False, False, False)
        self.mouse: Mouse = Mouse(0, 0, time.time())

    def is_dead(self):
        return self.died_at != None

    def kill(self):
        self.died_at = time.time()
        self.scale = 0
        self.state.x = -100
        self.state.y = -100

    def spawn(self, x, y):
        self.state.x = x
        self.state.y = y
        self.center_x = x
        self.center_y = y
        self.scale = WIZARD_SCALING
        self.state.dashing = False
        self.state.casting = False
        self.died_at = None

    def set_state(self, state: PlayerState):
        self.state = state
        self.center_x = self.state.x
        self.center_y = self.state.y
        self.change_x = self.state.dx
        self.change_y = self.state.dy

    def update_animation(self, delta_time: float = 1 / 60):
        anim_speed = 0.1
        self.cur_texture += 1
        cur_frame = int(self.cur_texture * anim_speed) % 4

        if self.state.casting:
            if self.mouse.x < self.state.x and self.facing == consts.RIGHT:
                self.facing = consts.LEFT
            elif self.mouse.x > self.state.x and self.facing == consts.LEFT:
                self.facing = consts.RIGHT
        else:
            if self.state.dx < 0 and self.facing == consts.RIGHT:
                self.facing = consts.LEFT
            elif self.state.dx > 0 and self.facing == consts.LEFT:
                self.facing = consts.RIGHT

        if self.state.dx != 0 or self.state.dy != 0:
            # Player is moving
            self.texture = self.run_textures[self.facing][cur_frame]
        else:
            # Player is idle
            self.texture = self.idle_textures[self.facing][cur_frame]

    def update_press_map(self, press_map):
        self.press_map = press_map

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self.mouse.x = x
        self.mouse.y = y

    def dash_towards(self, x: int, y: int):
        self.state.dashing = True
        self.dash_start = time.time()
        self.state.dx = x - self.state.x
        self.state.dy = y - self.state.y

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if self.is_dead():
            return
        if button == MOUSE_BUTTON_LEFT:
            if self.state.casting:
                return
            if time.time() - self.dash_start < DASH_COOLDOWN / 1000.0:
                return
            self.dash_towards(x, y)

        if button == MOUSE_BUTTON_RIGHT:
            if self.state.dashing:
                return
            self.mouse = Mouse(x, y, time.time())
            self.state.casting = True

    def on_mouse_release(self, x: int, y: int, button: int, spawn_spell):
        if self.is_dead():
            return
        if button == MOUSE_BUTTON_RIGHT and self.state.casting:
            # Initialize the projectile
            self.state.casting = False
            self.mouse.x = x
            self.mouse.y = y
            dx = self.mouse.x - self.center_x
            dy = self.mouse.y - self.center_y
            pos = Vec2(self.center_x, self.center_y)
            vel = Vec2(dx, dy)
            vel.normalize()
            vel.scale(consts.get_speed(time.time() - self.mouse.time_down))
            spawn_spell(pos, vel, self)

    def unmanaged_update(self, delta_time: float):
        """
        A function to update the player state according to movements
        NOTE: This function is only called if this player should respond to player inputs
        """
        if self.is_dead():
            return
        if self.state.dashing:
            # Dashes happen in straight lines, no room for input
            return
        # Do all the actual math
        self.state.dx = 0
        self.state.dy = 0
        if self.press_map.left and not self.press_map.right:
            self.state.dx = -1
        if not self.press_map.left and self.press_map.right:
            self.state.dx = 1
        if self.press_map.up and not self.press_map.down:
            self.state.dy = 1
        if not self.press_map.up and self.press_map.down:
            self.state.dy = -1

    def on_update(self, delta_time):
        if self.is_dead():
            return
        if self.state.dashing and time.time() - self.dash_start > DASH_LENGTH / 1000.0:
            self.state.dashing = False
        if not self.is_managed:
            self.unmanaged_update(delta_time)
        SPEED = PLAYER_SPEED
        if self.state.casting:
            SPEED = CAST_SPEED
        if self.state.dashing:
            SPEED = DASH_SPEED
        total_speed = math.sqrt(self.state.dx**2 + self.state.dy**2)
        if total_speed > 0:
            self.state.dx /= total_speed
            self.state.dy /= total_speed
            self.state.dx *= SPEED
            self.state.dy *= SPEED
        self.change_x, self.change_y = self.state.dx, self.state.dy
        self.state.x, self.state.y = self.center_x, self.center_y
        self.update_animation()

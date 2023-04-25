from typing import List
import arcade
from arcade import key as KEY
import consts
from player import Player
from spell import Spell
from utils import KeyInput, Vec2
from ai import AI, EasyAI
import time
import random


class NerfGoliath(arcade.Window):
    """
    The highest level game controller
    """

    def __init__(self):
        super().__init__(consts.SCREEN_WIDTH, consts.SCREEN_HEIGHT, consts.SCREEN_TITLE)
        self.scene: arcade.Scene = arcade.Scene()
        self.player: Player = Player(is_managed=False)
        self.ai: List[AI] = []
        self.ai_list: arcade.SpriteList = arcade.SpriteList()
        self.spell_list: arcade.SpriteList = arcade.SpriteList()
        self.press_map = KeyInput(False, False, False, False)
        self.camera: arcade.Camera = arcade.Camera()
        self.grass_texture = arcade.load_texture("assets/images/grass.png")
        arcade.set_background_color((6, 6, 6))

    def setup(self):
        """
        Does the work of setting up the game. Useful to have outside of __init__
        so resetting is easy.
        """

        self.scene = arcade.Scene()
        self.camera = arcade.Camera(self.width, self.height)

        # Sprites
        self.scene.add_sprite_list("spells", False)
        self.spell_list = self.scene.get_sprite_list("spells")

        def do_draw():
            for spell in self.spell_list:
                if type(spell) != Spell:
                    continue
                spell.on_draw()

        self.spell_list.draw = do_draw

        self.player = Player(is_managed=False)
        self.scene.add_sprite("player", self.player)

        self.ai_player = Player(is_managed=True)
        self.ai = [EasyAI(self.ai_player)]
        self.scene.add_sprite_list("ai", False)
        self.ai_list = self.scene.get_sprite_list("ai")
        for bot in self.ai:
            self.ai_list.append(bot.player)

    def refocus_camera(self):
        screen_center_x = self.player.center_x - (self.camera.viewport_width / 2)
        screen_center_y = self.player.center_y - (self.camera.viewport_height / 2)

        # Don't let camera travel past 0
        if screen_center_x < 0:
            screen_center_x = 0
        if screen_center_y < 0:
            screen_center_y = 0
        player_centered = (screen_center_x, screen_center_y)

        self.camera.move_to(player_centered)

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""
        if key == KEY.A:
            self.press_map.left = True
        if key == KEY.D:
            self.press_map.right = True
        if key == KEY.S:
            self.press_map.down = True
        if key == KEY.W:
            self.press_map.up = True
        self.player.update_press_map(self.press_map)

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""
        if key == KEY.A:
            self.press_map.left = False
        if key == KEY.D:
            self.press_map.right = False
        if key == KEY.S:
            self.press_map.down = False
        if key == KEY.W:
            self.press_map.up = False
        self.player.update_press_map(self.press_map)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self.player.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        self.player.on_mouse_press(x, y, button, modifiers)

    def spawn_spell(self, pos: Vec2, vel: Vec2, parent: Player):
        new_spell = Spell(pos, vel, parent)
        self.spell_list.append(new_spell)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        self.player.on_mouse_release(x, y, button, self.spawn_spell)

    def handle_collisions(self):
        agents = [self.player] + [bot.player for bot in self.ai]
        for agent in agents:
            if agent.is_dead():
                continue
            colls = arcade.check_for_collision_with_list(agent, self.spell_list)
            killed = False
            for col in colls:
                if type(col) == Spell:
                    if col.exploding:
                        killed = True
                    elif col.parent != agent:
                        # col.explode()
                        killed = True
            if killed:
                agent.kill()

    def handle_respawns(self):
        agents = [self.player] + [bot.player for bot in self.ai]
        for agent in agents:
            if (
                agent.died_at != None
                and time.time() - agent.died_at > consts.RESPAWN_TIMER
            ):
                x = random.randint(0, consts.SCREEN_WIDTH)
                y = random.randint(0, consts.SCREEN_HEIGHT)
                agent.spawn(x, y)

    def on_update(self, delta_time):
        for bot in self.ai:
            bot.think(self.scene, self.spawn_spell)
        self.scene.on_update(delta_time)
        # self.refocus_camera()

    def update(self, delta):
        self.scene.update()
        self.handle_collisions()
        self.handle_respawns()

    def on_draw(self):
        """Render the screen."""
        self.clear()
        self.camera.use()

        self.scene.draw()
        if self.player.state.casting:
            arcade.draw_circle_outline(
                self.player.indicator_pos[0],
                self.player.indicator_pos[1],
                25,
                border_width=3,
                color=(0, 0, 0),
            )


def main():
    window = NerfGoliath()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()

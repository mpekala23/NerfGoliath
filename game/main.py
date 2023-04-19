import arcade
from arcade import key as KEY
import consts
from player import Player

test = 1


class NerfGoliath(arcade.Window):
    """
    The highest level game controller
    """

    def __init__(self):
        super().__init__(consts.SCREEN_WIDTH, consts.SCREEN_HEIGHT, consts.SCREEN_TITLE)
        self.scene: arcade.Scene = arcade.Scene()
        self.player_list: arcade.SpriteList = arcade.SpriteList()
        self.wall_sprite: arcade.SpriteList = arcade.SpriteList()
        self.press_map = {"left": False, "right": False, "up": False, "down": False}
        self.camera: arcade.Camera = arcade.Camera()
        arcade.set_background_color(arcade.color_from_hex_string("#f8f8f8"))

    def setup(self):
        """
        Does the work of setting up the game. Useful to have outside of __init__
        so resetting is easy.
        """

        self.scene = arcade.Scene()
        self.camera = arcade.Camera(self.width, self.height)

        # Create the Sprite lists
        self.scene.add_sprite_list("player")
        self.scene.add_sprite_list("walls", use_spatial_hash=True)

        # Sprites
        self.player_list = arcade.SpriteList()
        self.player = Player()
        self.player.setup()
        self.player_list.append(self.player)
        self.scene.add_sprite("player", self.player)

        self.wall_list = arcade.SpriteList(use_spatial_hash=True)

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

    def on_draw(self):
        """Render the screen."""
        self.clear()
        self.camera.use()
        self.scene.draw()

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""
        if key == KEY.A:
            self.press_map["left"] = True
        if key == KEY.D:
            self.press_map["right"] = True
        if key == KEY.S:
            self.press_map["down"] = True
        if key == KEY.W:
            self.press_map["up"] = True
        self.player.update_press_map(self.press_map)

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""
        if key == KEY.A:
            self.press_map["left"] = False
        if key == KEY.D:
            self.press_map["right"] = False
        if key == KEY.S:
            self.press_map["down"] = False
        if key == KEY.W:
            self.press_map["up"] = False
        self.player.update_press_map(self.press_map)

    def on_update(self, delta_time):
        """Movement and game logic"""
        self.player.frame(delta_time)
        self.player_list.update()
        # self.refocus_camera()


def main():
    window = NerfGoliath()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()

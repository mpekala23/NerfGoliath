import sys

sys.path.append("..")

from typing import List
import arcade
from arcade import key as KEY
from arcade import MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT
import game.consts as consts
from game.player_sprite import PlayerSprite
from game.spell_sprite import SpellSprite
from schema import KeyInput, MouseInput, Vec2, InputState, GameState, Spell
from typing import Callable, Mapping
import random

SPELL_SPEED = 12


class Game(arcade.Window):
    """
    A class that runs the game for a player but is limited in how it can interact with the game.
    Really, this class's job is just to render the game and get player input. All the state
    updates and complicated coordinated logic should be handled in the agent.
    """

    def __init__(
        self,
        on_update_key: Callable[[KeyInput], None],
        on_update_mouse: Callable[[MouseInput], None],
    ):
        # Use the library
        super().__init__(consts.SCREEN_WIDTH, consts.SCREEN_HEIGHT, consts.SCREEN_TITLE)
        self.scene: arcade.Scene = arcade.Scene()

        # Get ready for input
        self.key_input = KeyInput(False, False, False, False)
        self.mouse_input = MouseInput(Vec2(0, 0), False, False)
        self.on_update_key = on_update_key
        self.on_update_mouse = on_update_mouse

        # Set up the game
        self.camera: arcade.Camera = arcade.Camera(
            consts.SCREEN_WIDTH, consts.SCREEN_HEIGHT
        )
        arcade.set_background_color((6, 6, 6))

        # Setup the sprite lists
        self.scene.add_sprite_list("players", False)
        self.player_list = self.scene.get_sprite_list("players")
        self.scene.add_sprite_list("spells", False)
        self.spell_list = self.scene.get_sprite_list("spells")

    def setup_for_players(self, player_names: list[str]):
        self.player_list.clear()
        self.spell_list.clear()
        for player_name in player_names:
            new_player = PlayerSprite(player_name)
            self.player_list.append(new_player)
        # No idea why, but if the sprite list ever becomes empty it bugs out
        # Need to always have this offscreen sprite in it
        dummy_spell = Spell(2, Vec2(-100, -100), Vec2(0, 0))
        dummy_sprite = SpellSprite(dummy_spell)
        self.spell_list.append(dummy_sprite)

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""
        if key == KEY.A:
            self.key_input.left = True
        if key == KEY.D:
            self.key_input.right = True
        if key == KEY.S:
            self.key_input.down = True
        if key == KEY.W:
            self.key_input.up = True
        self.on_update_key(self.key_input)

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""
        if key == KEY.A:
            self.key_input.left = False
        if key == KEY.D:
            self.key_input.right = False
        if key == KEY.S:
            self.key_input.down = False
        if key == KEY.W:
            self.key_input.up = False
        self.on_update_key(self.key_input)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        self.mouse_input.pos = Vec2(x, y)
        self.on_update_mouse(self.mouse_input)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        self.mouse_input.pos = Vec2(x, y)
        if button == MOUSE_BUTTON_LEFT:
            self.mouse_input.left = True
        if button == MOUSE_BUTTON_RIGHT:
            self.mouse_input.right = True
        self.on_update_mouse(self.mouse_input)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        self.mouse_input.pos = Vec2(x, y)
        if button == MOUSE_BUTTON_LEFT:
            self.mouse_input.left = False
        if button == MOUSE_BUTTON_RIGHT:
            self.mouse_input.right = False
        self.on_update_mouse(self.mouse_input)

    def on_update(self, delta_time):
        self.scene.on_update(delta_time)

    def update(self, delta):
        self.scene.update()

    def on_draw(self):
        """Render the screen."""
        self.clear()
        self.camera.use()
        self.scene.draw()

    @staticmethod
    def update_game_state(
        game_state: GameState,
        input_map: Mapping[str, InputState],
        last_input_map: Mapping[str, InputState],
    ):
        """
        Does the work of updating all the game state
        NOTE: Modifies game_state directly
        """
        # First handle player input and movement
        for px in range(len(game_state.players)):
            # First update the player's position and such
            old_player = game_state.players[px]
            p_inp = input_map[old_player.id]
            new_player = PlayerSprite.get_new_state(old_player, p_inp)
            game_state.players[px] = new_player
            # Then see what spells we need to spawn
            old_p_inp = last_input_map[old_player.id]
            if old_p_inp.mouse_input.right and not p_inp.mouse_input.right:
                # Right button was released between updates
                pos = new_player.pos
                vel = p_inp.mouse_input.pos - new_player.pos
                vel.normalize()
                vel *= SPELL_SPEED
                state = Spell(game_state.spell_count + 1, pos, vel)
                game_state.spells.append(state)
                game_state.spell_count += 1

        # Then move all the spells
        new_spells: list[Spell] = []
        for sx in range(len(game_state.spells)):
            old_spell = game_state.spells[sx]
            new_spell = Spell(
                old_spell.id, old_spell.pos + old_spell.vel, old_spell.vel
            )
            if (
                new_spell.pos.x >= 0
                and new_spell.pos.x < consts.SCREEN_WIDTH
                and new_spell.pos.y >= 0
                and new_spell.pos.y < consts.SCREEN_HEIGHT
            ):
                new_spells.append(new_spell)
        game_state.spells = new_spells

    def take_game_state(self, game_state: GameState):
        """
        This function implements the logic needed by non-leader games to simply update
        everything to match the gamestate that they will receive over the wire
        """
        id_to_player_map = {player.id: player for player in game_state.players}

        for player_sprite in self.player_list:
            if type(player_sprite) != PlayerSprite:
                continue
            player_sprite.state = id_to_player_map[player_sprite.state.id]

        id_to_spell_map = {spell.id: spell for spell in game_state.spells}
        in_sprite_list = set()

        # Update the state of all existing spells, killing those that don't exist anymore
        kill_list = []
        for spell_sprite in self.spell_list:
            if type(spell_sprite) != SpellSprite:
                continue
            if (
                spell_sprite.state.id not in id_to_spell_map
                and spell_sprite.state.id != -1
            ):
                kill_list.append(spell_sprite)
            else:
                spell_sprite.state = id_to_spell_map[spell_sprite.state.id]
                in_sprite_list.add(spell_sprite.state.id)
        for spell in kill_list:
            spell.kill()

        # Add the new spells
        for spell in game_state.spells:
            if spell.id in in_sprite_list:
                continue
            new_sprite = SpellSprite(spell)
            self.spell_list.append(new_sprite)

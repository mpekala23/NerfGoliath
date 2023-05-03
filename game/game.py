import sys

sys.path.append("..")

from typing import List, Union
import arcade
from arcade import key as KEY
from arcade import MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT
import game.consts as consts
from game.player_sprite import PlayerSprite
from game.spell_sprite import SpellSprite
from schema import KeyInput, MouseInput, Vec2, InputState, GameState, Spell
from typing import Callable, Mapping
import time
from threading import Lock
import random

SPELL_SPEED_MIN = 7
SPELL_SPEED_MAX = 20
SPELL_SPEED_SCALING = 8


class Game(arcade.Window):
    """
    A class that runs the game for a player but is limited in how it can interact with the game.
    Really, this class's job is just to render the game and get player input. All the state
    updates and complicated coordinated logic should be handled in the agent.
    """

    def __init__(
        self,
        screen_name: str,
        on_update_key: Callable[[KeyInput], None],
        on_update_mouse: Callable[[MouseInput], None],
        my_name: str,
    ):
        # Use the library
        super().__init__(consts.SCREEN_WIDTH, consts.SCREEN_HEIGHT, screen_name)
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
        # A helper variable to time how long the player holds the right button
        self.rdown_at: Union[float, None] = None
        # A list of spells to remove on the next update frame
        # NOTE: Has to be done like this to prevent thread rendering issues
        self.spell_kill_list: list[SpellSprite] = []
        self.spell_kill_lock = Lock()
        self.my_name = my_name
        self.last_game_state: Union[GameState, None] = None

    def setup_for_players(self, player_names: list[str]):
        self.player_list.clear()
        self.spell_list.clear()
        for player_name in player_names:
            new_player = PlayerSprite(player_name, is_you=player_name == self.my_name)
            self.player_list.append(new_player)
        # No idea why, but if the sprite list ever becomes empty it bugs out
        # Need to always have this offscreen sprite in it
        dummy_spell = Spell(2, Vec2(-1000, -1000), Vec2(0, 0), "test")
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
            self.rdown_at = time.time()
        self.on_update_mouse(self.mouse_input)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        self.mouse_input.pos = Vec2(x, y)
        if button == MOUSE_BUTTON_LEFT:
            self.mouse_input.left = False
        if button == MOUSE_BUTTON_RIGHT:
            self.mouse_input.right = False
            self.mouse_input.rheld_for = (
                0 if self.rdown_at == None else time.time() - self.rdown_at
            )
            self.rdown_at = None
        self.on_update_mouse(self.mouse_input)

    def on_update(self, delta_time):
        self.scene.on_update(delta_time)
        with self.spell_kill_lock:
            for spell in self.spell_kill_list:
                spell.kill()
            self.spell_kill_list = []

    def update(self, delta):
        self.scene.update()

    def on_draw(self):
        """Render the screen."""
        self.clear()
        self.camera.use()
        self.scene.draw()
        # Draw the score above the player
        if self.last_game_state != None:
            for player in self.last_game_state.players:
                if not player.is_alive:
                    continue
                arcade.draw_text(
                    f"{player.score}",
                    player.pos.x,
                    player.pos.y + 25,
                    (255, 255, 255),
                    14,
                    font_name="Kenney Pixel Square",
                )

    @staticmethod
    def update_game_state(
        game_state: GameState, input_map: Mapping[str, InputState], david: str
    ):
        """
        Does the work of updating all the game state
        NOTE: Modifies game_state directly
        """
        # First handle player input
        for px in range(len(game_state.players)):
            # First update the player's position and such
            if not game_state.players[px].is_alive:
                continue
            old_player = game_state.players[px]
            p_inp = input_map[old_player.id]
            new_player = PlayerSprite.get_new_state(old_player, p_inp)
            new_player.is_david = new_player.id == david
            game_state.players[px] = new_player
            # Then see what spells we need to spawn
            if (
                old_player.is_casting
                and not new_player.is_casting
                and new_player.is_alive
            ):
                speed = (
                    SPELL_SPEED_MIN + p_inp.mouse_input.rheld_for * SPELL_SPEED_SCALING
                )
                speed = min(SPELL_SPEED_MAX, speed)
                # Right button was released between updates
                pos = new_player.pos
                vel = p_inp.mouse_input.pos - new_player.pos
                vel.normalize()
                vel *= speed
                state = Spell(game_state.spell_count + 1, pos, vel, old_player.id)
                game_state.spells.append(state)
                game_state.spell_count += 1

        # Then move all the spells
        new_spells: list[Spell] = []
        for sx in range(len(game_state.spells)):
            old_spell = game_state.spells[sx]
            new_spell = SpellSprite.get_new_state(old_spell)
            if (
                new_spell.pos.x >= 0
                and new_spell.pos.x < consts.SCREEN_WIDTH
                and new_spell.pos.y >= 0
                and new_spell.pos.y < consts.SCREEN_HEIGHT
            ):
                new_spells.append(new_spell)
        game_state.spells = new_spells

        # Then handle collisions
        for player in game_state.players:
            for spell in game_state.spells:
                if player.id == spell.creator:
                    continue
                dist_sq = (player.pos.x - spell.pos.x) ** 2 + (
                    player.pos.y - 4 - spell.pos.y
                ) ** 2
                radius = 16 * (
                    consts.DAVID_SCALING if player.is_david else consts.GOLIATH_SCALING
                )
                if dist_sq < radius**2 and player.is_alive:
                    player.time_till_respawn = 40
                    player.is_alive = False
                    spell.pos.y = -1000
                    spell.pos.x = -1000
                    for p in game_state.players:
                        if p.id == spell.creator:
                            p.score += 1
                            print(
                                f"Player {player.id} was hit by {p.id}'s spell! {p.id} Score: {p.score}"
                            )
            if player.time_till_respawn > 0:
                player.time_till_respawn -= 1
            if player.time_till_respawn == 1:
                player.is_alive = True
                player.pos.x = random.randint(0, consts.SCREEN_WIDTH)
                player.pos.y = random.randint(0, consts.SCREEN_HEIGHT)

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
        for spell_sprite in self.spell_list:
            if type(spell_sprite) != SpellSprite:
                continue
            if (
                spell_sprite.state.id not in id_to_spell_map
                and spell_sprite.state.id != -1
            ):
                with self.spell_kill_lock:
                    self.spell_kill_list.append(spell_sprite)
            else:
                spell_sprite.state = id_to_spell_map[spell_sprite.state.id]
                in_sprite_list.add(spell_sprite.state.id)

        # Add the new spells
        for spell in game_state.spells:
            if spell.id in in_sprite_list:
                continue
            new_sprite = SpellSprite(spell)
            self.spell_list.append(new_sprite)

        self.last_game_state = game_state

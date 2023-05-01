from connections.manager import ConnectionManager
from connections.machine import Machine
from game.game import Game
from schema import KeyInput, MouseInput, Vec2, InputState, GameState, Player
import arcade
from threading import Thread
import time


class Agent:
    """
    The actual program that each player will run to participate in the game
    """

    def __init__(self, machine: Machine):
        self.identity = machine

        # Function to pass the connection manager to let it update gamestate
        def update_game_state(game_state: GameState):
            self.game_state = game_state

        self.conman = ConnectionManager(machine, update_game_state)
        self.conman.initialize()
        self.key_input: KeyInput = KeyInput(False, False, False, False)
        self.mouse_input: MouseInput = MouseInput(Vec2(0, 0), False, False)
        self.game = Game(self.on_update_key, self.on_update_mouse)
        self.game.activate()
        # Note that because the rendering must happen on the main thread, this spins up
        # another thread which will be doing the updates
        self.game_state = GameState(
            [Player(name, Vec2(0, 0), Vec2(0, 0)) for name in self.conman.input_map],
            [],
        )
        self.game.setup_for_players([name for name in self.conman.input_map])
        self.agent_loop_thread = Thread(target=self.agent_loop)
        self.agent_loop_thread.start()
        self.game.run()

    def on_update_key(self, key_input: KeyInput):
        """
        Handy setter to allow the game to update the key input via callback
        """
        self.key_input = key_input

    def on_update_mouse(self, mouse_input: MouseInput):
        """
        Handy setter to allow the game to update the mouse input via callback
        """
        self.mouse_input = mouse_input

    def agent_loop(self):
        AGENT_SLEEP = 0.01
        last_input_map = self.conman.input_map
        while True:
            new_last = self.conman.input_map.copy()
            input_state = InputState(
                self.key_input,
                MouseInput(
                    self.mouse_input.pos, self.mouse_input.left, self.mouse_input.right
                ),
            )
            self.conman.broadcast_input(input_state)
            if self.conman.is_leader():
                Game.update_game_state(
                    self.game_state, self.conman.input_map, last_input_map
                )
                self.conman.broadcast_game_state(self.game_state)
            last_input_map = new_last.copy()
            self.game.take_game_state(self.game_state)
            time.sleep(AGENT_SLEEP)


def create_agent(machine: Machine) -> Agent:
    """
    Creates an agent for a given machine
    """
    return Agent(machine)

from connections.consts import BLANK_MACHINE, NEGOTIATOR_IP, NEGOTIATOR_PORT
from connections.manager import ConnectionManager
from game.game import Game
from schema import (
    KeyInput,
    MouseInput,
    Vec2,
    InputState,
    GameState,
    Player,
    ConnectRequest,
    ConnectResponse,
    Machine,
    wire_decode,
)
from threading import Thread, Lock
import time
import random
import socket
from game.consts import SCREEN_WIDTH, SCREEN_HEIGHT
import sys


class Agent:
    """
    The actual program that each player will run to participate in the game
    """

    def __init__(self, name: str):
        # Function to pass the connection manager to let it update gamestate
        def update_game_state(game_state: GameState):
            self.game_state = game_state

        self.identity: Machine = self.negotiate(name)
        self.conman = ConnectionManager(self.identity, update_game_state)
        self.conman.initialize()
        self.key_input: KeyInput = KeyInput(False, False, False, False)
        self.mouse_input: MouseInput = MouseInput(Vec2(0, 0), False, False)
        self.game = Game(
            self.identity.name,
            self.on_update_key,
            self.on_update_mouse,
            self.identity.name,
        )
        self.game.activate()
        # Note that because the rendering must happen on the main thread, this spins up
        # another thread which will be doing the updates
        self.game_state = GameState(
            "A",
            [
                Player(
                    name,
                    Vec2(
                        random.randint(0, SCREEN_WIDTH),
                        random.randint(0, SCREEN_HEIGHT),
                    ),
                    Vec2(0, 0),
                )
                for name in self.conman.input_map
            ],
            [],
        )
        # Makes sure we don't double create projectiles
        self.input_lock = Lock()
        self.game.setup_for_players([name for name in self.conman.input_map])
        self.agent_loop_thread = Thread(target=self.agent_loop)
        self.agent_loop_thread.start()
        self.game.run()

    def negotiate(self, name: str) -> Machine:
        while True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.connect((NEGOTIATOR_IP, NEGOTIATOR_PORT))
                sock.send(ConnectRequest(name).encode())
                data = sock.recv(1024)
                if not data or len(data) <= 0:
                    raise Exception("Negotiator did not respond")
                resp = wire_decode(data)
                if type(resp) != ConnectResponse:
                    raise Exception("Negotiator did not understand")
                if not resp.success:
                    raise Exception("Negotiator rejected connection")
                mach_data = sock.recv(2048)
                if not mach_data or len(mach_data) <= 0:
                    raise Exception("Negotiator did not send machine data")
                mach = wire_decode(mach_data)
                if type(mach) != Machine:
                    raise Exception("Negotiator did not send machine data")
                return mach
            except Exception as e:
                pass
            time.sleep(random.uniform(0.5, 1.0))

    def on_update_key(self, key_input: KeyInput):
        """
        Handy setter to allow the game to update the key input via callback
        """
        with self.input_lock:
            self.key_input = key_input

    def on_update_mouse(self, mouse_input: MouseInput):
        """
        Handy setter to allow the game to update the mouse input via callback
        """
        with self.input_lock:
            self.mouse_input = mouse_input

    def agent_loop(self):
        FPS = 45
        AGENT_SLEEP = 1.0 / FPS
        while True:
            with self.input_lock:
                input_state = InputState(
                    self.key_input,
                    MouseInput(
                        self.mouse_input.pos,
                        self.mouse_input.left,
                        self.mouse_input.right,
                        self.mouse_input.rheld_for,
                    ),  # Copy to avoid mutability errors
                )
            self.conman.broadcast_input(
                input_state,
            )
            with self.conman.leader_lock:
                if self.conman.is_leader():
                    Game.update_game_state(
                        self.game_state,
                        self.conman.input_map,
                        david=self.identity.name,
                    )

                    self.game_state.next_leader = min(
                        self.game_state.players, key=lambda p: p.score
                    ).id

                    self.conman.broadcast_game_state(self.game_state)
            self.game.take_game_state(self.game_state)
            time.sleep(AGENT_SLEEP)


def create_agent(name: str) -> Agent:
    """
    Creates an agent for a given machine
    """
    return Agent(name)


if __name__ == "__main__":
    create_agent(sys.argv[1])
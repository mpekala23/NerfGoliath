from connections.consts import (
    NEGOTIATOR_IP,
    NEGOTIATOR_PORT,
    LEADER_CHANGE_COOLDOWN,
)
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
from game.consts import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
import sys
import arcade
import game.ai as cpu
from typing import Union


class Agent:
    """
    The actual program that each player will run to participate in the game
    """

    def __init__(self, name: str, ai: Union[cpu.AI, None] = None):
        self.alive = True

        # Function to pass the connection manager to let it update gamestate
        def update_game_state(game_state: GameState):
            self.game_state = game_state

        self.fout = open(f"output/{name}.txt", "w")
        self.ai = ai
        (self.identity, am_leader) = self.negotiate(name)
        self.conman = ConnectionManager(self.identity, update_game_state, am_leader)
        self.conman.initialize()
        self.key_input: KeyInput = KeyInput(False, False, False, False)
        self.mouse_input: MouseInput = MouseInput(Vec2(0, 0), False, False)
        self.game = Game(
            self.identity.name,
            self.on_update_key if self.ai == None else cpu.dummy_keys,
            self.on_update_mouse if self.ai == None else cpu.dummy_mouse,
            self.identity.name,
        )
        self.game.activate()
        # A ticker to limit leader change updates
        self.ticks_since_leader_change = 0
        # Note that because the rendering must happen on the main thread, this spins up
        # another thread which will be doing the updates
        self.game_state = GameState(
            self.identity.name if am_leader else "",
            [
                Player(
                    name,
                    Vec2(
                        random.randint(0, SCREEN_WIDTH),
                        random.randint(0, SCREEN_HEIGHT),
                    ),
                    Vec2(0, 0),
                )
                for name in (
                    list(self.conman.input_sockets.keys()) + [self.identity.name]
                )
            ],
            [],
        )
        # Makes sure we don't double create projectiles
        self.input_lock = Lock()
        self.game.setup_for_players(
            [name for name in self.conman.input_sockets] + [self.identity.name]
        )
        self.agent_loop_thread = Thread(target=self.agent_loop)
        self.agent_loop_thread.start()

    def run(self):
        self.game.run()

    def negotiate(self, name: str) -> tuple[Machine, bool]:
        """
        Connect to the negotiator to get a machine id to play the game
        """
        while self.alive:
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
                return (mach, resp.is_leader)
            except Exception as e:
                pass
            time.sleep(random.uniform(0.5, 1.0))
        raise Exception("Can't negotiate")

    def on_update_key(self, key_input: KeyInput):
        """
        Handy setter to allow the game to update the key input via callback
        """
        with self.input_lock:
            self.key_input = key_input
            input_state = InputState(self.key_input, self.mouse_input)
            self.conman.broadcast_input(
                input_state,
            )

    def on_update_mouse(self, mouse_input: MouseInput):
        """
        Handy setter to allow the game to update the mouse input via callback
        """
        with self.input_lock:
            self.mouse_input = mouse_input
            input_state = InputState(self.key_input, self.mouse_input)
            self.conman.broadcast_input(
                input_state,
            )

    def agent_loop(self):
        AGENT_SLEEP = 1.0 / FPS
        was_leader_last_tick = False

        while self.alive:
            with self.conman.leader_lock:
                is_leader_this_tick = self.conman.is_leader()
                if is_leader_this_tick:
                    if not was_leader_last_tick:
                        self.ticks_since_leader_change = 0

                    Game.update_game_state(
                        self.game_state,
                        self.conman.input_map,
                        david=self.identity.name,
                    )

                    if self.ticks_since_leader_change >= LEADER_CHANGE_COOLDOWN:
                        worst = self.game_state.get_worst()
                        self.game_state.next_leader = worst

                    self.ticks_since_leader_change += 1

                    self.conman.broadcast_game_state(self.game_state)
                elif self.conman.should_backup_broadcast():
                    self.conman.broadcast_game_state(self.game_state)

            self.game.take_game_state(self.game_state)

            if self.ai != None and random.randint(0, 6) == 0:
                next_input = self.ai.get_move(self.game_state)
                self.on_update_key(next_input.key_input)
                self.on_update_mouse(next_input.mouse_input)

            was_leader_last_tick = is_leader_this_tick
            time.sleep(AGENT_SLEEP)

    def kill(self):
        self.conman.kill()
        self.alive = False
        self.fout.close()


def create_agent(name: str, use_ai: bool = False):
    """
    Creates an agent for a given machine
    """
    agent = False
    ai = None
    if use_ai:
        ai = cpu.RandomAI(name)
    try:
        agent = Agent(name, ai)
        agent.run()
    except:
        pass
    if agent:
        agent.kill()
    arcade.exit()


if __name__ == "__main__":
    create_agent(sys.argv[1])

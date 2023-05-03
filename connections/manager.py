import sys

sys.path.append("..")

import time
import socket
from typing import Union, Callable
from queue import Queue
from threading import Thread, Lock
from utils import print_error, print_success
from schema import Ping, InputState, GameState, Machine, Wireable


class ConnectionManager:
    """
    Handles the dirty work of opening sockets to the other machines.
    Abstracts to allow machines to operate at the level of sending
    messages based on machine name, ignoring underlying sockets.
    """

    def __init__(
        self, identity: Machine, update_game_state: Callable[[GameState], None]
    ):
        self.identity = identity
        self.is_primary = False  # Is this the primary?
        self.living_siblings: list[Machine] = []
        self.id_map: dict[str, Machine] = {}
        self.alive = True
        self.input_sockets = {}
        self.input_map_lock = Lock()
        self.input_map = {self.identity.name: InputState()}
        self.game_sockets = {}
        self.leader_lock = Lock()
        self.leader_name: Union[str, None] = "A"
        self.wires_received: Queue[Wireable] = Queue()
        self.update_game_state = update_game_state

    def initialize(self):
        """
        Does blocking work to establish connections to peers
        """
        # First it should establish connections to all other internal machines
        listen_thread = Thread(target=self.listen_internally)
        connect_thread = Thread(target=self.handle_internal_connections)
        listen_thread.start()
        connect_thread.start()
        listen_thread.join()
        connect_thread.join()

        # Start the threads that will continuously get input
        for name, sock in self.input_sockets.items():
            # Be sure to consume with the internal flag set to True
            consumer_thread = Thread(
                target=self.consume_input,
                args=(
                    name,
                    sock,
                ),
            )
            consumer_thread.start()

        # Start the threads that will continuously get gamestate
        for name, sock in self.game_sockets.items():
            # Be sure to consume with the internal flag set to True
            consumer_thread = Thread(
                target=self.consume_game_state,
                args=(
                    name,
                    sock,
                ),
            )
            consumer_thread.start()

        # Once all the servers are up we start doing health checks
        health_listen_thread = Thread(target=self.listen_health)
        health_listen_thread.start()
        health_probe_thread = Thread(target=self.probe_health)
        health_probe_thread.start()
        print_success(f"{self.identity.name} is all set!")

    def listen_internally(self, sock=None):
        """
        Listens for incoming internal connections. Adds a connection to the socket
        map once connected, and repeats num_listens times.
        """
        # Setup the socket

        input_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        game_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        input_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        game_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        input_sock.bind((self.identity.host_ip, self.identity.input_port))
        game_sock.bind((self.identity.host_ip, self.identity.game_port))
        input_sock.listen()
        game_sock.listen()
        # Listen the specified number of times
        listens_completed = 0
        try:
            while listens_completed < self.identity.num_listens:
                # Accept the input connection
                input_conn, _ = input_sock.accept()
                # Send the connector our identity
                input_conn.send(self.identity.encode())
                # Get the name of the machine that connected
                id = Machine.decode(input_conn.recv(2048))
                self.id_map[id.name] = id
                # Add the connection to the map
                self.input_sockets[id.name] = input_conn
                self.input_map[id.name] = InputState()

                # Accept the game_state connection
                game_conn, _ = game_sock.accept()
                # Add the connection to the map
                self.game_sockets[id.name] = game_conn

                listens_completed += 1
            input_sock.close()
            game_sock.close()
        except Exception as e:
            input_sock.close()
            game_sock.close()

    def listen_health(self, sock=None):
        """
        Listens for incoming health checks, responds with PingResponse
        """
        if sock == None:
            self.health_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.health_socket = sock
        self.health_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.health_socket.bind((self.identity.host_ip, self.identity.health_port))
        self.health_socket.listen()
        try:
            while self.alive:
                conn, _ = self.health_socket.accept()
                conn.recv(2048)
                conn.send(Ping().encode())
                conn.close()
        except:
            self.health_socket.close()

    def probe_health(self, sock_arg=None):
        """
        Sends a health check to every sibling regularly
        """
        FREQUENCY = 3  # seconds
        time.sleep(FREQUENCY)
        while self.alive:
            for sibling in self.living_siblings:
                sock = (
                    sock_arg
                    if sock_arg
                    else socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                )
                sock.settimeout(FREQUENCY)
                try:
                    sock.connect((sibling.host_ip, sibling.health_port))
                    sock.send(Ping().encode())
                    sock.recv(2048)
                    sock.close()
                except:
                    print_error(f"Machine {sibling.name} is dead")
                    self.living_siblings.remove(sibling)
            if sock_arg:
                # For testing purposes
                break
            time.sleep(FREQUENCY)

    def connect_internally(self, info: list[Union[str, int]], sock=None):
        """
        Connects to the machine with the given name
        NOTE: Can/is expected to sometimes throw errors
        """
        # Setup the input socket
        input_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        input_sock.connect((info[0], info[1]))
        # Send the machine our identity
        input_sock.send(self.identity.encode())
        # Get the Machine obj of the machine we just connected to
        id = Machine.decode(input_sock.recv(2048))
        self.id_map[id.name] = id
        # Add the connection to the map
        self.input_sockets[id.name] = input_sock
        self.input_map[id.name] = InputState()

        # Setup the game socket
        game_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        game_sock.connect((id.host_ip, id.game_port))
        # Add the connection to the map
        self.game_sockets[id.name] = game_sock

    def consume_input(self, name, conn):
        """
        Once a connection to the input thread is established, continuously listen
        for messages and update the input of the player accordingly
        """
        try:
            while True:
                # Get the message
                msg = conn.recv(2048)
                if not msg or len(msg) <= 0:
                    raise Exception("Connection closed")
                state = InputState.decode(msg)
                with self.input_map_lock:
                    self.input_map[name] = state
        except Exception:
            conn.close()

    def consume_game_state(self, name, conn):
        """
        Listens to game from each server. If it ever receives game state from a server
        that it does not currently think is the leader, it simply drops the packet
        """
        try:
            while True:
                # Get the message
                msg = conn.recv(2048)
                if not msg or len(msg) <= 0:
                    raise Exception("Connection closed")
                with self.leader_lock:
                    if name != self.leader_name:
                        continue
                    state = GameState.decode(msg)
                    self.update_game_state(state)
                    self.leader_name = state.next_leader
        except Exception as e:
            conn.close()

    def handle_internal_connections(self):
        """
        Handles the connections to other machines
        """
        # Connect to the machines in the connection list
        for info in self.identity.connections:
            connected = False
            while not connected:
                try:
                    self.connect_internally(info)
                    connected = True
                except Exception:
                    print_error(f"Failed to connect to {info}, retrying in 1 second")
                    time.sleep(1)

    def is_leader(self):
        """
        Helper function that makes leader-dependent actions more readable
        """
        return self.leader_name == self.identity.name

    def broadcast_input(self, input_state: InputState):
        """
        Broadcasts this machine's input state to all other machines in the system
        """
        # TODO: For efficiency only do this broadcast on changes
        with self.input_map_lock:
            self.input_map[self.identity.name] = input_state
            for name in self.input_sockets:
                self.input_sockets[name].send(
                    self.input_map[self.identity.name].encode()
                )

    def broadcast_game_state(self, game_state: GameState):
        """
        Can only be called when this agent is the leader.
        Assumes that the leader lock is already held
        """
        assert self.is_leader()
        self.leader_name = game_state.next_leader
        for name in self.game_sockets:
            self.game_sockets[name].send(game_state.encode())

    def kill(self):
        """
        Kills the connection manager
        """
        self.alive = False
        for sock in list(self.input_sockets.values()):
            # Helps prevent the weird "address is already in use" error
            try:
                sock.shutdown(1)
            except Exception:
                # Makes sure that we at least close every socket
                pass
            sock.close()
        if self.health_socket:
            self.health_socket.close()

import sys

sys.path.append("..")

import time
import socket
from typing import Union, Callable
from queue import Queue
from threading import Thread, Lock
from utils import print_error, print_success
from schema import (
    Ping,
    CommsRequest,
    CommsResponse,
    InputState,
    GameState,
    Machine,
    Wireable,
    ConnectRequest,
    ConnectResponse,
    wire_decode,
    Event,
)
from connections.consts import (
    WATCHER_IP,
    WATCHER_PORT,
    TICKS_PER_WATCH,
)
import random
import errors
import tests.mocks.mock_socket as mock_socket
from game.consts import NUM_PLAYERS, FPS


class ConnectionManager:
    """
    Handles the dirty work of opening sockets to the other machines.
    Abstracts to allow machines to opterate at the level of messages,
    forgetting about sockets
    """

    def __init__(
        self,
        identity: Machine,
        update_game_state: Callable[[GameState], None],
        is_leader: bool,
    ):
        self.identity = identity
        self.update_game_state = update_game_state
        self.alive = True
        self.watcher_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.input_sockets: dict[str, Union[socket.socket, mock_socket.socket]] = {}
        self.input_map_lock = Lock()
        self.input_map: dict[str, InputState] = {self.identity.name: InputState()}
        self.game_sockets: dict[str, Union[socket.socket, mock_socket.socket]] = {}
        self.leader_lock = Lock()
        self.leader_name: Union[str, None] = self.identity.name if is_leader else None
        self.health_sockets: dict[str, Union[socket.socket, mock_socket.socket]] = {}
        self.health_map: dict[str, int] = {}
        # Maps machine name to place to go for reconnection
        self.reconnect_map: dict[str, list[str | int]] = {}
        self.watcher_ticks: dict[str, int] = {"input": 0, "game": 0}
        self.last_inp_broadcast = time.time()  # Rate limit our broadcasts
        self.need_to_hear_from: Union[str, None] = None

    def register_connection(
        self, conn: Union[socket.socket, mock_socket.socket], req: CommsRequest, to: str
    ):
        """
        Once we have established a connection, handle the logic of updating
        the correct socket on this class to use it in the future
        """
        self.reconnect_map[to] = req.info
        if req.comms_type == "input":
            existed = to in self.input_sockets
            self.input_sockets[to] = conn
            if not existed:
                consume_thread = Thread(target=self.consume_input, args=(to,))
                consume_thread.start()
        elif req.comms_type == "game":
            existed = to in self.game_sockets
            self.game_sockets[to] = conn
            if not existed:
                consume_thread = Thread(target=self.consume_game_state, args=(to,))
                consume_thread.start()
        elif req.comms_type == "watcher":
            self.watcher_sock = conn
        elif req.comms_type == "health":
            self.health_sockets[to] = conn
        else:
            raise errors.UnknownComms(req.comms_type)

    def listen(self, isock: Union[mock_socket.socket, None] = None):
        """
        A function (ideally to be run in it's own thread) that is always listening
        for new connections and dealing with them
        NOTE: sock parameter only for unit testing
        """
        if isock == None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            sock = isock
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(5)
        sock.bind((self.identity.host_ip, self.identity.port))
        sock.listen()
        while self.alive:
            try:
                conn, addr = sock.accept()
                # FIRST: Receive the request from the other player
                data = conn.recv(2048)
                if not data or len(data) == 0:
                    print_error("ERROR: Can't get comms req")
                    conn.close()
                    continue
                req = wire_decode(data)
                if type(req) != CommsRequest:
                    # The first thing they send must be a comms request
                    resp = CommsResponse(self.identity.name, False)
                    conn.send(resp.encode())
                    conn.close()
                    continue
                # THEN: If all is good register the connection and send response
                self.register_connection(conn, req, req.name)
                resp = CommsResponse(self.identity.name, True)
                conn.send(resp.encode())
            except socket.timeout:
                # Have the listen thread stop every 5 seconds to check that
                # the connection manager is still alive
                pass
            except errors.InvalidMessage as e:
                print_error(f"ERROR: Unknown message {e.args}")
            except Exception as e:
                print_error(f"ERROR: Listen thread died {e.args}")
                break

    def connect(
        self,
        info: list[str | int],
        req: CommsRequest,
        isock: Union[mock_socket.socket, None] = None,
    ):
        connected = False
        while not connected and self.alive:
            try:
                # FIRST: Connect and send the request
                if isock == None:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                else:
                    sock = isock
                sock.connect((info[0], info[1]))
                sock.send(req.encode())
                data = sock.recv(2048)
                if not data or len(data) == 0:
                    print_error(f"ERROR: No response from {info}")
                    time.sleep(0.5 + random.random() * 2)
                    continue
                resp = wire_decode(data)
                if type(resp) != CommsResponse or resp.accepted == False:
                    print_error(f"ERROR: Invalid response from {info}")
                    continue
                # THEN: If all is good register the connection
                self.register_connection(sock, req, resp.name)
                connected = True
                # Remember the connection info in case we need to reconnect later
                self.reconnect_map[resp.name] = info
            except errors.InvalidMessage as e:
                print_error(f"ERROR: Unknown message {e.args}")
            except Exception as e:
                if e.args[0] == 61:
                    # Connection refused error
                    time.sleep(0.5 + random.random() * 2)
                    continue
                print_error(f"ERROR: Connect thread died without connecting {e.args}")
                break

    def initialize(self):
        """
        Initializes all the sockets/listeners that will be needed
        """
        # First connect to the watcher
        watch_req = CommsRequest(
            self.identity.name, [self.identity.host_ip, self.identity.port], "watcher"
        )
        self.connect([WATCHER_IP, WATCHER_PORT], watch_req)
        # Then set up our connection listener
        listen_thread = Thread(target=self.listen)
        listen_thread.start()
        # Next connect to our peers
        for peer in self.identity.connections:
            # We need 3 connections with each peer
            for type in ["input", "game", "health"]:
                req = CommsRequest(
                    self.identity.name,
                    [self.identity.host_ip, self.identity.port],
                    type,
                )
                self.connect(peer, req)
        # Finally, spin until we've heard from everyone
        while len(self.input_sockets) < NUM_PLAYERS - 1:
            time.sleep(0.5)

    def log_event(self, event: Event):
        """
        Logs an event to the watcher
        """
        if event.event_type == "input":
            self.watcher_ticks["input"] = (
                self.watcher_ticks["input"] + random.randint(0, 2)
            ) % TICKS_PER_WATCH
            if self.watcher_ticks["input"] <= 2:
                self.watcher_sock.send(event.encode())
        if event.event_type == "game":
            self.watcher_ticks["game"] = (
                self.watcher_ticks["game"] + random.randint(0, 2)
            ) % TICKS_PER_WATCH
            if self.watcher_ticks["game"] == 0:
                self.watcher_sock.send(event.encode())

    def consume_input(self, name):
        """
        A thread that continuously watches for input updates from a connection
        """
        conn = self.input_sockets[name]
        while self.alive:
            try:
                msg = conn.recv(2048)
                if not msg or len(msg) <= 0:
                    raise errors.CommsDied(f"Died consuming input from {name}")
                wired = wire_decode(msg)
                if type(wired) != InputState:
                    raise errors.InvalidMessage(msg.decode())
                self.input_map[name] = wired
            except errors.InvalidMessage:
                continue
            except errors.CommsDied:
                # TODO: Mark the death, deal with it elsewhere
                break
            except Exception as e:
                print_error(f"ERROR: consume_input died for unknown reason {e.args}")
                break
        conn.close()

    def consume_game_state(self, name):
        """
        A thread that continuously watches for game updates
        """
        conn = self.game_sockets[name]
        while self.alive:
            try:
                msg = conn.recv(2048)
                if not msg or len(msg) <= 0:
                    raise errors.CommsDied(f"Died consuming state from {name}")
                state = wire_decode(msg)
                if type(state) != GameState:
                    raise errors.InvalidMessage(msg.decode())
                with self.leader_lock:
                    if self.leader_name == None:
                        self.leader_name = state.next_leader
                    if name != self.leader_name:
                        continue
                    if name == self.need_to_hear_from:
                        self.need_to_hear_from = None
                    self.update_game_state(state)
                    self.leader_name = state.next_leader
            except errors.InvalidMessage:
                continue
            except errors.CommsDied:
                # TODO: Mark the death, deal with it elsewhere
                break
            except Exception as e:
                continue
        conn.close()

    def is_leader(self):
        """
        Helper function that makes leader-dependent actions more readable
        """
        return self.leader_name == self.identity.name

    def should_backup_broadcast(self):
        """
        Helper function to determine if this agent should broadcast because
        they were recently the leader but haven't yet heard from the new leader
        """
        return self.need_to_hear_from != None

    def broadcast_input(self, input_state: InputState):
        """
        Broadcasts this machine's input state to all other machines in the system
        """
        with self.input_map_lock:
            diff = 1.0 / FPS
            if time.time() - self.last_inp_broadcast < diff:
                return
            self.last_inp_broadcast = time.time()
            event = Event("input", self.identity.name, "delta")
            self.input_map[self.identity.name] = input_state
            for name in self.input_sockets:
                self.input_sockets[name].send(
                    self.input_map[self.identity.name].encode()
                )
                event.sink = name
                self.log_event(event)

    def broadcast_game_state(self, game_state: GameState):
        """
        Assumes that the leader lock is already held
        Called when this identity is the leader OR the are waiting to hear
        back from the new leader
        """
        if (
            self.leader_name == self.identity
            and game_state.next_leader != self.leader_name
        ):
            # A change is coming
            self.need_to_hear_from = game_state.next_leader
        self.leader_name = game_state.next_leader
        for name in self.game_sockets:
            self.game_sockets[name].sendall(game_state.encode())
            self.log_event(Event("game", self.identity.name, name))

    def kill(self):
        """
        Kills the connection manager
        """
        self.alive = False
        for sock in (
            list(self.input_sockets.values())
            + list(self.game_sockets.values())
            + list(self.health_sockets.values())
            + [self.watcher_sock]
        ):
            # Helps prevent the weird "address is already in use" error
            try:
                sock.close()
            except Exception:
                # Makes sure that we at least close every socket
                pass

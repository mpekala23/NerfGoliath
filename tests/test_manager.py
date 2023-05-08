import pytest
import sys
from mocks.mock_socket import socket
import time
from threading import Thread

sys.path.append("..")

from connections.manager import ConnectionManager, TICKS_PER_WATCH
import schema


def get_blank_conman() -> ConnectionManager:
    def dummy_update_game_state(_):
        pass

    id = schema.Machine("test", "localhost", 8000, [])
    return ConnectionManager(id, dummy_update_game_state, False)


def get_dummy_socket() -> socket:
    return socket(-1, -1)


def dummy_func(name):
    pass


class WatchFunc:
    def __init__(self):
        self.calls = []

    def func(self, *args, **kwargs):
        self.calls.append(args)


def test_register_connection():
    conman = get_blank_conman()
    conman.consume_game_state = dummy_func
    conman.consume_input = dummy_func
    sock = get_dummy_socket()

    input_req = schema.CommsRequest("test", ["localhost", 6], "input")
    game_req = schema.CommsRequest("test", ["localhost", 6], "game")
    watch_req = schema.CommsRequest("test", ["localhost", 6], "watcher")
    health_req = schema.CommsRequest("test", ["localhost", 6], "health")

    for req in [input_req, game_req, watch_req, health_req]:
        conman.register_connection(sock, req, "to")

    for d in [conman.input_sockets, conman.game_sockets, conman.health_sockets]:
        assert "to" in d

    assert conman.watcher_sock == sock


def test_listen():
    conman = get_blank_conman()
    sock = get_dummy_socket()
    sock.add_fake_send(schema.CommsRequest("name", ["localhost", 6], "input").encode())
    listen_thread = Thread(target=conman.listen, args=(sock,))
    listen_thread.start()
    time.sleep(0.5)
    conman.alive = False
    listen_thread.join()
    assert "name" in conman.input_sockets
    assert sock.has_listened
    assert len(sock.sent) == 1
    assert conman.reconnect_map["name"] == ["localhost", 6]


def test_connect():
    conman = get_blank_conman()
    sock = get_dummy_socket()
    info = ["localhost", 6]
    req = schema.CommsRequest("name", ["localhost", 6], "input")
    sock.add_fake_send(schema.CommsResponse("other", True).encode())
    conman.connect(info, req, sock)
    assert "other" in conman.input_sockets
    assert sock.connected_to == (info[0], info[1])
    assert len(sock.sent) == 1
    assert conman.reconnect_map["other"] == info


def test_initialize():
    conman = get_blank_conman()
    # Set up ways of checking if functions are called
    cwatch = WatchFunc()
    lwatch = WatchFunc()
    conman.connect = cwatch.func
    conman.listen = lwatch.func
    # Fill up the input sockets to avoid infinite loop at the end
    conman.input_sockets = {str(v): get_dummy_socket() for v in range(8)}
    # Add a peer that this machine should connect to
    conman.identity.connections = [["localhost", 6]]
    conman.initialize()

    # Make sure we've connected to the right places
    assert len(cwatch.calls) == 4
    assert (
        type(cwatch.calls[0][1]) == schema.CommsRequest
        and cwatch.calls[0][1].comms_type == "watcher"
    )
    assert (
        type(cwatch.calls[1][1]) == schema.CommsRequest
        and cwatch.calls[1][1].comms_type == "input"
    )
    assert (
        type(cwatch.calls[2][1]) == schema.CommsRequest
        and cwatch.calls[2][1].comms_type == "game"
    )
    assert (
        type(cwatch.calls[3][1]) == schema.CommsRequest
        and cwatch.calls[3][1].comms_type == "health"
    )
    assert len(lwatch.calls) == 1


def test_log_event():
    # Setup dummy conmans and socket, then make sure that log events pushes them to the watcher
    # NOTE: This is the only testing we do on the watcher, since it is primarily a debugging tool

    conman = get_blank_conman()
    sock = get_dummy_socket()
    conman.watcher_sock = sock
    ievent = schema.Event("input", "source", "sink")
    gevent = schema.Event("game", "source", "sink")
    conman.log_event(ievent)
    conman.log_event(gevent)

    assert sock.sent == [b"einput@source@sink$", b"egame@source@sink$"]


def test_consume_input():
    conman = get_blank_conman()
    sock = get_dummy_socket()
    conman.input_sockets["test"] = sock

    # Create fake input state and make sure it gets put into the input_map
    fake_input = schema.InputState()
    sock.add_fake_send(fake_input.encode())

    conman.consume_input("test")
    assert conman.input_map["test"] == fake_input


def test_consume_game_state_normal():
    conman = get_blank_conman()
    sock = get_dummy_socket()
    conman.game_sockets["test"] = sock

    # Create fake game state and make sure it gets called by update game state
    fake_state = schema.GameState(("new", 0), [], [])
    sock.add_fake_send(fake_state.encode())

    watch = WatchFunc()
    conman.update_game_state = watch.func
    consume = Thread(target=conman.consume_game_state, args=("test",))
    consume.start()

    time.sleep(0.5)
    conman.alive = False
    time.sleep(0.5)

    assert watch.calls[0] == (fake_state,)


def test_consume_game_state_illogical():
    conman = get_blank_conman()
    sock = get_dummy_socket()
    conman.game_sockets["test"] = sock

    # Game state with a lower logical value should be ignored
    conman.leader = ("other", 2)
    fake_state = schema.GameState(("new", 0), [], [])
    sock.add_fake_send(fake_state.encode())

    watch = WatchFunc()
    conman.update_game_state = watch.func
    consume = Thread(target=conman.consume_game_state, args=("test",))
    consume.start()

    time.sleep(0.5)
    conman.alive = False
    time.sleep(0.5)

    assert len(watch.calls) == 0


def test_is_leader():
    conman = get_blank_conman()
    conman.leader = None
    assert not conman.is_leader()
    conman.leader = ("other", 0)
    assert not conman.is_leader()
    conman.leader = ("test", 0)
    assert conman.is_leader()


def test_should_i_broadcast_backup():
    conman = get_blank_conman()
    conman.need_to_hear_from = None
    assert not conman.should_backup_broadcast()
    conman.need_to_hear_from = "other"
    assert conman.should_backup_broadcast()


def test_broadcast_input():
    conman = get_blank_conman()
    sock = get_dummy_socket()
    conman.last_inp_broadcast = 0

    conman.input_sockets = {"other": sock}
    istate = schema.InputState()
    conman.broadcast_input(istate)

    assert sock.sent == [istate.encode()]


def test_broadcast_gamestate_normal():
    conman = get_blank_conman()
    sock = get_dummy_socket()

    conman.game_sockets = {"other": sock}
    conman.leader = None
    conman.log_event = lambda event: None

    fake_state = schema.GameState(("new", 0), [], [])
    conman.broadcast_game_state(fake_state)

    assert conman.leader == ("new", 0)
    assert sock.sent == [fake_state.encode()]


def test_broadcast_gamestate_backup():
    conman = get_blank_conman()
    sock = get_dummy_socket()

    conman.game_sockets = {"other": sock}
    conman.leader = ("test", 0)
    conman.log_event = lambda event: None

    fake_state = schema.GameState(("new", 0), [], [])
    conman.broadcast_game_state(fake_state)

    assert conman.leader == ("new", 0)
    assert sock.sent == [fake_state.encode()]
    assert conman.need_to_hear_from == "new"

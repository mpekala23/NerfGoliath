import pytest
import sys
from mocks.mock_socket import socket
import time
from threading import Thread

sys.path.append("..")

from connections.manager import ConnectionManager
import schema


def get_blank_conman() -> ConnectionManager:
    def dummy_update_game_state(_):
        pass

    id = schema.Machine("test", "localhost", 8000, [])
    return ConnectionManager(id, dummy_update_game_state, False)


def get_dummy_socket() -> socket:
    return socket(-1, -1)


def test_register_connection():
    conman = get_blank_conman()
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

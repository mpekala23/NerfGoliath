import pytest
import sys
from mocks.mock_socket import socket
import time
from threading import Thread

sys.path.append("..")

from agent import Agent, create_agent
from game import consts as gconsts
from connections import consts as cconsts
from connections.manager import ConnectionManager
import schema


def get_blank_conman() -> ConnectionManager:
    def dummy_update_game_state(_):
        pass

    id = schema.Machine("test", "localhost", 8000, [])
    return ConnectionManager(id, dummy_update_game_state, False)


def get_blank_agent() -> Agent:
    return Agent("test", None, True)


def get_dummy_socket() -> socket:
    return socket(-1, -1)


class WatchFunc:
    def __init__(self):
        self.calls = []

    def func(self, *args, **kwargs):
        self.calls.append(args)


def test_negotiate():
    # Make sure that players interact with the negotiator to register
    # for the game properly

    agent = get_blank_agent()
    sock = get_dummy_socket()
    sock.add_fake_send(schema.ConnectResponse(True, True).encode())
    sock.add_fake_send(schema.Machine("A", "localhost", 2, []).encode())
    (mach, leader) = agent.negotiate("A", sock)

    assert sock.connected_to == (cconsts.NEGOTIATOR_IP, cconsts.NEGOTIATOR_PORT)
    assert sock.sent[0] == schema.ConnectRequest("A").encode()
    assert mach.encode() == schema.Machine("A", "localhost", 2, []).encode()
    assert leader


def test_on_update_key():
    istate = schema.InputState()
    agent = get_blank_agent()
    watch = WatchFunc()
    agent.conman.broadcast_input = watch.func
    agent.mouse_input = istate.mouse_input
    agent.on_update_key(istate.key_input)
    assert watch.calls[0][0].encode() == istate.encode()


def test_on_update_mouse():
    istate = schema.InputState()
    agent = get_blank_agent()
    watch = WatchFunc()
    agent.conman.broadcast_input = watch.func
    agent.key_input = istate.key_input
    agent.on_update_mouse(istate.mouse_input)
    assert watch.calls[0][0].encode() == istate.encode()

import pytest
import sys
from mocks.mock_socket import socket
import time
from threading import Thread

sys.path.append("..")

from connections.negotiator import Negotiator
from game import consts as gconsts
from connections import consts as cconsts
import schema


def get_blank_negotiator() -> Negotiator:
    return Negotiator()


def get_dummy_socket() -> socket:
    return socket(-1, -1)


def test_negotiate():
    neg = get_blank_negotiator()
    sock = get_dummy_socket()

    sock.add_fake_send(schema.ConnectRequest("A").encode())
    # Try to join with a name that already exists
    sock.add_fake_send(schema.ConnectRequest("A").encode())
    sock.add_fake_send(schema.ConnectRequest("B").encode())
    sock.add_fake_send(schema.ConnectRequest("C").encode())
    sock.add_fake_send(schema.ConnectRequest("D").encode())
    sock.add_fake_send(schema.ConnectRequest("E").encode())

    neg.negotiate(sock)

    # Check that the correct number of machines were created
    assert len(neg.machines) == gconsts.NUM_PLAYERS
    assert len(neg.socket_map) == gconsts.NUM_PLAYERS

    # Get access to all the things that the negotiator sent
    decoded = [schema.wire_decode(bs) for bs in sock.sent]
    # A should be the leader
    assert type(decoded[0]) == schema.ConnectResponse and decoded[0].is_leader
    # The second A should be rejected
    assert type(decoded[1]) == schema.ConnectResponse and decoded[1].success == False

    # The negotiator should send machine info to A with no connections
    assert (
        type(decoded[6]) == schema.Machine
        and decoded[6].name == "A"
        and len(decoded[6].connections) == 0
    )

    # The negotiator should send machine info to E with four connections
    assert (
        type(decoded[10]) == schema.Machine
        and decoded[10].name == "E"
        and len(decoded[10].connections) == 4
    )

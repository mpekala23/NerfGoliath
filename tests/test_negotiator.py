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

"""
This file tests the schema of the game. Basically it tests that all the data
classes are as expected and serialize/deserialize correctly
"""

import pytest
import sys

sys.path.append("..")
from schema import (
    Vec2,
    Spell,
    Player,
    GameState,
    KeyInput,
    MouseInput,
    InputState,
    wire_decode,
)

SPELL = Spell(Vec2(1, 2), Vec2(3, 4), 100)
PLAYER = Player("test", Vec2(1, 2), Vec2(3, 4))
GAME_STATE = GameState([PLAYER], [SPELL])
KEY_INPUT = KeyInput(True, True, False, True)
MOUSE_INPUT = MouseInput(Vec2(1, 6), True, False)
INPUT_STATE = InputState(KEY_INPUT, MOUSE_INPUT)


def test_Vec2_encode_decode():
    assert Vec2.decode(Vec2(1, 2).encode()) == Vec2(1, 2)
    assert wire_decode(Vec2(1, 2).encode()) == Vec2(1, 2)


def test_Spell_encode_decode():
    assert Spell.decode(SPELL.encode()) == SPELL
    assert wire_decode(SPELL.encode()) == SPELL


def test_Player_encode_decode():
    assert Player.decode(PLAYER.encode()) == PLAYER
    assert wire_decode(PLAYER.encode()) == PLAYER


def test_GameState_encode_decode():
    assert GameState.decode(GAME_STATE.encode()) == GAME_STATE
    assert wire_decode(GAME_STATE.encode()) == GAME_STATE


def test_KeyInput_encode_decode():
    assert KeyInput.decode(KEY_INPUT.encode()) == KEY_INPUT
    assert wire_decode(KEY_INPUT.encode()) == KEY_INPUT


def test_MouseInput_encode_decode():
    assert MouseInput.decode(MOUSE_INPUT.encode()) == MOUSE_INPUT
    assert wire_decode(MOUSE_INPUT.encode()) == MOUSE_INPUT


def test_InputState_encode_decode():
    assert InputState.decode(INPUT_STATE.encode()) == INPUT_STATE
    assert wire_decode(INPUT_STATE.encode()) == INPUT_STATE

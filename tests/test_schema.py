"""
This file tests the schema of the game. Basically it tests that all the data
classes are as expected and serialize/deserialize correctly
"""

import pytest
import sys

sys.path.append("..")
from schema import Vec2, Spell, Player, GameState

SPELL = Spell(Vec2(1, 2), Vec2(3, 4), 100)
PLAYER = Player("test", Vec2(1, 2), Vec2(3, 4))
GAME_STATE = GameState([PLAYER], [SPELL])


def test_Vec2_encode_decode():
    assert Vec2.decode(Vec2(1, 2).encode()) == Vec2(1, 2)


def test_Spell_encode_decode():
    assert Spell.decode(SPELL.encode()) == SPELL


def test_Player_encode_decode():
    assert Player.decode(PLAYER.encode()) == PLAYER


def test_GameState_encode_decode():
    assert GameState.decode(GAME_STATE.encode()) == GAME_STATE

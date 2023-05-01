from main import NerfGoliath
from typing import List
import arcade
from arcade import key as KEY
import consts
from player import Player
from spell import Spell
from utils import KeyInput, Vec2
from ai import AI, EasyAI
import time
import random

class GameFollower(NerfGoliath):
    """
    Class for the follower window
    """

    
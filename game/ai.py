import sys

sys.path.append("..")

import random
from schema import GameState, InputState, KeyInput, MouseInput, Vec2
from game.consts import SCREEN_WIDTH, SCREEN_HEIGHT


def dummy_keys(_):
    pass


def dummy_mouse(_):
    pass


class AI:
    def __init__(self, player_id: str):
        self.player_id = player_id

    def get_move(self, game_state: GameState) -> InputState:
        raise NotImplementedError()


class RandomAI(AI):
    def __init__(self, player_id: str, odds_switch=6):
        super().__init__(player_id)
        self.odds_switch = odds_switch

    def get_move(self, game_state: GameState) -> InputState:
        keys = KeyInput(
            True if random.randint(0, self.odds_switch) == 0 else False,
            True if random.randint(0, self.odds_switch) == 0 else False,
            True if random.randint(0, self.odds_switch) == 0 else False,
            True if random.randint(0, self.odds_switch) == 0 else False,
        )
        mouse = MouseInput(
            Vec2(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)),
            True if random.randint(0, self.odds_switch) == 0 else False,
            True if random.randint(0, self.odds_switch) == 0 else False,
        )
        return InputState(keys, mouse)

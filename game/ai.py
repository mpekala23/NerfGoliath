import arcade
from player import Player, PlayerState
import consts
import random
from utils import Vec2
import time


class AI:
    def __init__(self, player: Player):
        self.player = player

    def think(self, scene: arcade.Scene, spawn_spell) -> None:
        pass


class EasyAI(AI):
    def __init__(self, player: Player):
        self.player = player
        self.player.state.dx = random.randint(1, 2)
        self.player.state.dy = random.randint(1, 2)
        self.time_down = time.time()

    def think(self, scene: arcade.Scene, spawn_spell) -> None:
        if self.player.is_dead():
            return
        # Update the position so that he bounces around in a lil box
        offLeft = self.player.state.x < 0
        offRight = self.player.state.x > consts.SCREEN_WIDTH
        if offLeft:
            self.player.state.dx = random.randint(1, 5)
        if offRight:
            self.player.state.dx = -random.randint(1, 5)

        offTop = self.player.state.y > consts.SCREEN_HEIGHT
        offBot = self.player.state.y < 0
        if offTop:
            self.player.state.dy = -random.randint(1, 5)
        if offBot:
            self.player.state.dy = random.randint(1, 5)

        if self.player.state.dx == 0 and self.player.state.dy == 0:
            self.player.state.dx = random.randint(1, 5)
            self.player.state.dy = random.randint(1, 5)

        # Fire a shot every now and then
        SHOT_RATE = 2 * 60
        RELEASE_RATE = 60
        FUZZ = 20
        if not self.player.state.casting and random.randint(0, SHOT_RATE) == 0:
            self.player.state.casting = True
            self.time_down = time.time()
        if self.player.state.casting:
            enemy = scene.get_sprite_list("player")
            if len(enemy) <= 0:
                self.player.state.casting = False
            else:
                self.player.mouse.x = enemy[0].center_x
                self.player.mouse.y = enemy[0].center_y
                shouldFire = random.randint(0, RELEASE_RATE) == 0
                if shouldFire:
                    pos = Vec2(self.player.state.x, self.player.state.y)
                    vel = Vec2(
                        self.player.mouse.x
                        - self.player.state.x
                        + random.randint(-FUZZ, FUZZ),
                        self.player.mouse.y
                        - self.player.state.y
                        + random.randint(-FUZZ, FUZZ),
                    )
                    vel.normalize()
                    vel.scale(consts.get_speed(time.time() - self.time_down))
                    spawn_spell(pos, vel, self.player)
                    self.player.state.casting = False

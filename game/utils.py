import math


class Mouse:
    def __init__(self, x: int, y: int, time_down: float):
        self.x = x
        self.y = y
        self.time_down = time_down


class KeyInput:
    def __init__(self, left: bool, right: bool, up: bool, down: bool):
        self.left = left
        self.right = right
        self.up = up
        self.down = down


class Vec2:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def normalized(self) -> "Vec2":
        if self.x == 0 and self.y == 0:
            return Vec2(0, 0)
        length = math.sqrt(self.x**2 + self.y**2)
        return Vec2(self.x / length, self.y / length)

    def normalize(self):
        if self.x == 0 and self.y == 0:
            return
        length = math.sqrt(self.x**2 + self.y**2)
        self.x /= length
        self.y /= length

    def scale(self, c):
        self.x *= c
        self.y *= c

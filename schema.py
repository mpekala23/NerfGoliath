from typing import List
from game import consts
import math


class Wireable:
    def __repr__(self):
        return str(self)

    @staticmethod
    def unique_char() -> str:
        raise NotImplementedError()

    def encode(self) -> str:
        raise NotImplementedError()

    @staticmethod
    def decode(s: str) -> "Wireable":
        raise NotImplementedError()


class Vec2(Wireable):
    """
    Simple custom vector to be passed around the game, with handy
    operator overloads.
    """

    @staticmethod
    def unique_char() -> str:
        return "v"

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __str__(self):
        return f"Vec2({float(self.x)}, {float(self.y)})"

    def __eq__(self, other):
        if type(other) != Vec2:
            return False
        return self.x == other.x and self.y == other.y

    def encode(self):
        data = (self.x, self.y)
        return f"{Vec2.unique_char()}{data[0]}@{data[1]}"

    @staticmethod
    def fromstr(s: str):
        x, y = s[4:-1].split(",")
        return Vec2(float(x), float(y))

    @staticmethod
    def decode(s: str) -> "Vec2":
        data = s[1:].split("@")
        return Vec2(float(data[0]), float(data[1]))

    def __add__(self, other):
        if type(other) != Vec2:
            raise TypeError(f"Cannot add Vec2 to {type(other)}")
        return Vec2(self.x + other.x, self.y + other.y)

    def __iadd__(self, other):
        if type(other) != Vec2:
            raise TypeError(f"Cannot add Vec2 to {type(other)}")
        self.x += other.x
        self.y += other.y
        return self

    def __sub__(self, other):
        if type(other) != Vec2:
            raise TypeError(f"Cannot subtract Vec2 from {type(other)}")
        return Vec2(self.x - other.x, self.y - other.y)

    def __isub__(self, other):
        if type(other) != Vec2:
            raise TypeError(f"Cannot subtract Vec2 from {type(other)}")
        self.x -= other.x
        self.y -= other.y
        return self

    def __mul__(self, c):
        return Vec2(self.x * c, self.y * c)

    def __imul__(self, c):
        self.x *= c
        self.y *= c
        return self

    def __truediv__(self, c):
        return Vec2(self.x / c, self.y / c)

    def __itruediv__(self, c):
        self.x /= c
        self.y /= c
        return self

    def __getitem__(self, key):
        if key == 0:
            return self.x
        elif key == 1:
            return self.y
        else:
            raise IndexError(f"Vec2 has no index {key}")

    @staticmethod
    def zero():
        return Vec2(0, 0)

    @staticmethod
    def left():
        return Vec2(-1, 0)

    @staticmethod
    def right():
        return Vec2(1, 0)

    @staticmethod
    def up():
        return Vec2(0, -1)

    @staticmethod
    def down():
        return Vec2(0, 1)

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


class Spell(Wireable):
    """
    The data that defines a spell, this should be sufficient
    """

    @staticmethod
    def unique_char() -> str:
        return "s"

    def __init__(self, pos: Vec2, ivel: Vec2, time_till_boom: float):
        self.pos = pos
        self.ivel = ivel
        self.time_till_boom = time_till_boom

    def __str__(self):
        return f"Spell({self.pos}, {self.ivel}, {float(self.time_till_boom)})"

    def __eq__(self, other):
        if type(other) != Spell:
            return False
        return str(self) == str(other)

    def encode(self):
        data = (self.pos.x, self.pos.y, self.ivel.x, self.ivel.y, self.time_till_boom)
        return f"{Spell.unique_char()}{data[0]}@{data[1]}@{data[2]}@{data[3]}@{data[4]}"

    @staticmethod
    def decode(s: str):
        data = s[1:].split("@")
        return Spell(
            Vec2(float(data[0]), float(data[1])),
            Vec2(float(data[2]), float(data[3])),
            float(data[4]),
        )


class Player(Wireable):
    """
    The data that defines a player
    """

    @staticmethod
    def unique_char() -> str:
        return "p"

    def __init__(
        self,
        id: str,
        pos: Vec2,
        vel: Vec2,
        is_alive: bool = True,
        time_till_respawn: float = 0,
        facing: int = consts.RIGHT,
        is_casting: bool = False,
    ):
        self.id = id
        self.pos = pos
        self.vel = vel
        self.is_alive = is_alive
        self.time_till_respawn = time_till_respawn
        self.facing = facing
        self.is_casting = is_casting

    def __str__(self):
        return f"Player({self.id}, {self.pos}, {self.vel}, {self.is_alive}, {float(self.time_till_respawn)}, {int(self.facing)}, {self.is_casting})"

    def __eq__(self, other):
        if type(other) != Player:
            return False
        return str(self) == str(other)

    def encode(self):
        data = (
            self.id,
            self.pos.x,
            self.pos.y,
            self.vel.x,
            self.vel.y,
            self.is_alive,
            self.time_till_respawn,
            self.facing,
            self.is_casting,
        )
        return f"{Player.unique_char()}{data[0]}@{data[1]}@{data[2]}@{data[3]}@{data[4]}@{data[5]}@{data[6]}@{data[7]}@{data[8]}"

    @staticmethod
    def decode(s: str):
        data = s[1:].split("@")
        return Player(
            data[0],
            Vec2(float(data[1]), float(data[2])),
            Vec2(float(data[3]), float(data[4])),
            data[5] == "True",
            float(data[6]),
            int(data[7]),
            data[8] == "True",
        )


class GameState(Wireable):
    """
    The data that defines the game state
    """

    @staticmethod
    def unique_char() -> str:
        return "g"

    def __init__(
        self,
        players: List[Player],
        spells: List[Spell],
    ):
        self.players = players
        self.spells = spells

    def __str__(self):
        return f"GameState(\n\t{self.players},\n\t{self.spells}\n)"

    def __eq__(self, other):
        if not isinstance(other, GameState):
            return False
        print("HERERERE", str(self), str(other))
        return str(self) == str(other)

    def encode(self):
        player_encodings = []
        for player in self.players:
            player_encodings.append(player.encode())
        spell_encodings = []
        for spell in self.spells:
            spell_encodings.append(spell.encode())
        result = GameState.unique_char()
        result += f"{','.join(player_encodings)}"
        result += "#"
        result += f"{','.join(spell_encodings)}"
        return result

    @staticmethod
    def decode(s: str):
        data = s[1:].split("#")
        player_data = data[0].split(",")
        spell_data = data[1].split(",")
        players = []
        for player in player_data:
            players.append(Player.decode(player))
        spells = []
        for spell in spell_data:
            spells.append(Spell.decode(spell))
        return GameState(players, spells)

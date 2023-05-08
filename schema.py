from game import consts
import math
import errors
import json
from typing import Union
from enum import Enum

DELIM = "$"


class Wireable:
    def __repr__(self):
        return str(self)

    @staticmethod
    def unique_char() -> str:
        raise NotImplementedError()

    def encode(self) -> bytes:
        raise NotImplementedError()

    @staticmethod
    def decode(s: bytes) -> "Wireable":
        raise NotImplementedError()


class Ping(Wireable):
    """
    A simple ping message to check if a server is still alive.
    """

    @staticmethod
    def unique_char() -> str:
        return "i"

    def __str__(self):
        return "Ping()"

    def encode(self):
        return f"{Ping.unique_char()}{DELIM}".encode()

    @staticmethod
    def decode(_) -> "Ping":
        return Ping()


class CommsRequest(Wireable):
    """
    A message that requests a connection to another player. It must specify the person
    who is connecting's name, as well as what kind of communication they need.
    Valid comms types are:
    - "input" for sending input updates
    - "game" for sending game state updates
    - "watcher" for sending log data to the watcher
    - "health" for sending health checks
    """

    @staticmethod
    def unique_char() -> str:
        return "1"

    def __init__(self, name: str, info: list[str | int], comms_type: str):
        self.name = name
        self.info = info
        self.comms_type = comms_type

    def __str__(self):
        return f"CommsRequest({self.name}, {self.info}, {self.comms_type})"

    def encode(self):
        return f"{CommsRequest.unique_char()}{self.name}@{self.info[0]}@{self.info[1]}@{self.comms_type}{DELIM}".encode()

    @staticmethod
    def decode(s: bytes) -> "CommsRequest":
        data = (s.decode())[1:].split("@")
        return CommsRequest(data[0], [data[1], int(data[2])], data[3])


class CommsResponse(Wireable):
    """
    A message that responds to a connection request. It must specify the person
    who is responding, as well as whether the connection was accepted
    """

    @staticmethod
    def unique_char() -> str:
        return "2"

    def __init__(self, name: str, accepted: bool):
        self.name = name
        self.accepted = accepted

    def __str__(self):
        return f"CommsResponse({self.name}, {self.accepted})"

    def encode(self):
        return (
            f"{CommsResponse.unique_char()}{self.name}@{self.accepted}{DELIM}".encode()
        )

    @staticmethod
    def decode(s: bytes) -> "CommsResponse":
        data = (s.decode())[1:].split("@")
        return CommsResponse(data[0], data[1] == "True")


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
        return f"{Vec2.unique_char()}{data[0]}@{data[1]}{DELIM}".encode()

    @staticmethod
    def decode(s: bytes) -> "Vec2":
        data = (s.decode())[1:].strip("$").split("@")
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

    def __init__(self, id: int, pos: Vec2, ivel: Vec2, creator: str):
        self.id = id
        self.pos = pos
        self.vel = ivel
        self.creator = creator

    def __str__(self):
        return f"Spell({self.id} {self.pos}, {self.vel}, {self.creator})"

    def __eq__(self, other):
        if type(other) != Spell:
            return False
        return str(self) == str(other)

    def encode(self):
        data = (self.id, self.pos.x, self.pos.y, self.vel.x, self.vel.y, self.creator)
        return f"{Spell.unique_char()}{data[0]}@{data[1]}@{data[2]}@{data[3]}@{data[4]}@{data[5]}{DELIM}".encode()

    @staticmethod
    def decode(s: bytes):
        data = (s.decode())[1:].strip("$").split("@")
        return Spell(
            int(float(data[0])),
            Vec2(float(data[1]), float(data[2])),
            Vec2(float(data[3]), float(data[4])),
            data[5],
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
        is_david: bool = False,
        score: int = 0,
    ):
        self.id = id
        self.pos = pos
        self.vel = vel
        self.is_alive = is_alive
        self.time_till_respawn = time_till_respawn
        self.facing = facing
        self.is_casting = is_casting
        self.is_david = is_david
        self.score = score

    def __str__(self):
        return f"Player({self.id}, {self.pos}, {self.vel}, {self.is_alive}, {float(self.time_till_respawn)}, {int(self.facing)}, {self.is_casting}, {self.is_david}, {self.score})"

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
            self.is_david,
            self.score,
        )
        return f"{Player.unique_char()}{data[0]}@{data[1]}@{data[2]}@{data[3]}@{data[4]}@{data[5]}@{data[6]}@{data[7]}@{data[8]}@{data[9]}@{data[10]}{DELIM}".encode()

    @staticmethod
    def decode(s: bytes):
        data = (s.decode())[1:].strip("$").split("@")
        return Player(
            data[0],
            Vec2(float(data[1]), float(data[2])),
            Vec2(float(data[3]), float(data[4])),
            data[5] == "True",
            float(data[6]),
            int(float(data[7])),
            data[8] == "True",
            data[9] == "True",
            int(float(data[10])),
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
        next_leader: tuple[str, int],
        players: list[Player],
        spells: list[Spell],
        spell_count: int = 0,
    ):
        self.next_leader = next_leader
        self.players = players
        self.spells = spells
        self.spell_count = spell_count

    def __str__(self):
        return f"GameState(\n\t{self.next_leader}\n\t{self.players},\n\t{self.spells},\n\t{self.spell_count}\n)"

    def __eq__(self, other):
        if not isinstance(other, GameState):
            return False
        return str(self) == str(other)

    def encode(self):
        player_encodings = []
        for player in self.players:
            player_encodings.append(str(player.encode())[2:-2])
        spell_encodings = []
        for spell in self.spells:
            spell_encodings.append(str(spell.encode())[2:-2])
        result = GameState.unique_char()
        result += f"{self.next_leader[0]}#{self.next_leader[1]}"
        result += "#"
        result += f"{','.join(player_encodings)}"
        result += "#"
        result += f"{','.join(spell_encodings)}"
        result += "#"
        result += f"{self.spell_count}"
        result += DELIM
        return result.encode()

    @staticmethod
    def decode(s: bytes):
        data = (s.decode())[1:].strip("$").split("#")
        next_leader = (data[0], int(float(data[1])))
        player_data = data[2].split(",")
        spell_data = data[3].split(",")
        players = []
        for player in player_data:
            if len(player) <= 0:
                continue
            players.append(Player.decode(player.encode()))
        spells = []
        for spell in spell_data:
            if len(spell) <= 0:
                continue
            spells.append(Spell.decode(spell.encode()))
        spell_count = int(float(data[4]))
        return GameState(next_leader, players, spells, spell_count)

    def get_worst(self) -> str:
        lowest = (1000, "Z")
        for player in self.players:
            if (
                player.score < lowest[0]
                or player.score == lowest[0]
                and player.id < lowest[1]
            ):
                lowest = (player.score, player.id)
        return lowest[1]


class KeyInput(Wireable):
    """
    The data that defines a key input
    """

    @staticmethod
    def unique_char() -> str:
        return "k"

    def __init__(self, left: bool, right: bool, up: bool, down: bool):
        self.left = left
        self.right = right
        self.up = up
        self.down = down

    def __str__(self):
        return f"KeyInput({self.left}, {self.right}, {self.up}, {self.down})"

    def __eq__(self, other):
        if type(other) != KeyInput:
            return False
        return str(self) == str(other)

    def encode(self):
        data = (self.left, self.right, self.up, self.down)
        return f"{KeyInput.unique_char()}{data[0]}@{data[1]}@{data[2]}@{data[3]}{DELIM}".encode()

    @staticmethod
    def decode(s: bytes):
        data = (s.decode())[1:].strip("$").split("@")
        return KeyInput(
            data[0] == "True", data[1] == "True", data[2] == "True", data[3] == "True"
        )


class MouseInput(Wireable):
    """
    The data that defines a mouse input
    """

    @staticmethod
    def unique_char() -> str:
        return "m"

    def __init__(self, pos: Vec2, left: bool, right: bool, rheld_for: float = 0.0):
        self.pos = pos
        self.left = left
        self.right = right
        self.rheld_for = rheld_for

    def __str__(self):
        return f"MouseInput({self.pos}, {self.left}, {self.right}, {self.rheld_for})"

    def __eq__(self, other):
        if type(other) != MouseInput:
            return False
        return str(self) == str(other)

    def encode(self):
        data = (self.pos.x, self.pos.y, self.left, self.right, self.rheld_for)
        return f"{MouseInput.unique_char()}{data[0]}@{data[1]}@{data[2]}@{data[3]}@{data[4]}{DELIM}".encode()

    @staticmethod
    def decode(s: bytes):
        data = (s.decode())[1:].strip("$").split("@")
        return MouseInput(
            Vec2(float(data[0]), float(data[1])),
            data[2] == "True",
            data[3] == "True",
            float(data[4]),
        )


class InputState(Wireable):
    """
    The data that defines the input state
    """

    @staticmethod
    def unique_char() -> str:
        return "n"

    def __init__(
        self,
        key_input: KeyInput = KeyInput(False, False, False, False),
        mouse_input: MouseInput = MouseInput(Vec2(0, 0), False, False),
    ):
        self.key_input = key_input
        self.mouse_input = mouse_input

    def __str__(self):
        return f"InputState({self.key_input}, {self.mouse_input})"

    def __eq__(self, other):
        if type(other) != InputState:
            return False
        return str(self) == str(other)

    def encode(self):
        return f"{InputState.unique_char()}{self.key_input.encode().decode()[:-1]}#{self.mouse_input.encode().decode()[:-1]}{DELIM}".encode()

    @staticmethod
    def decode(s: bytes):
        data = (s.decode())[1:].split("#")
        return InputState(
            KeyInput.decode(data[0].encode()), MouseInput.decode(data[1].encode())
        )


class ConnectRequest(Wireable):
    """
    A request that can be sent to the negotiator to join the game
    """

    @staticmethod
    def unique_char():
        return "c"

    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return f"ConnectRequest({self.name})"

    def __eq__(self, other):
        if type(other) != ConnectRequest:
            return False
        return str(self) == str(other)

    def encode(self):
        return f"{ConnectRequest.unique_char()}{self.name}{DELIM}".encode()

    @staticmethod
    def decode(s: bytes):
        data = (s.decode())[1:].strip("$").split("@")
        return ConnectRequest(data[0])


class ConnectResponse(Wireable):
    """
    What the negotiator sends in response to a client connecting
    """

    @staticmethod
    def unique_char():
        return "r"

    def __init__(self, success: bool, is_leader: bool = False):
        self.success = success
        self.is_leader = is_leader

    def __str__(self):
        return f"ConnectResponse({self.success}, {self.is_leader})"

    def __eq__(self, other):
        if type(other) != ConnectResponse:
            return False
        return str(self) == str(other)

    def encode(self):
        return f"{ConnectResponse.unique_char()}{self.success}@{self.is_leader}{DELIM}".encode()

    @staticmethod
    def decode(s: bytes):
        data = (s.decode())[1:].split("@")
        return ConnectResponse(data[0] == "True", data[1] == "True")


class Machine(Wireable):
    """
    A class that represents the identity of a machine. Most crucially
    this stores information about which ip/port the machine is listening
    on, as well as which other machines it is responsible for connecting
    to.
    """

    @staticmethod
    def unique_char():
        return "t"

    def __init__(
        self,
        name: str,
        host_ip: str,
        port: int,
        connections: list[list[Union[str, int]]],
    ) -> None:
        # The name of the machine
        self.name = name
        # The ip address the machine should listen on for new connections
        self.host_ip = host_ip
        # The port that the machine should accept new connections on
        self.port = port
        # The names of the machines that this machine should connect to
        self.connections = connections

    def __str__(self):
        return f"Machine({self.name}, {self.host_ip}, {self.port}, {self.connections})"

    def __eq__(self, other):
        if type(other) != Machine:
            return False
        return str(self) == str(other)

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    def encode(self):
        return (self.unique_char() + self.toJson() + DELIM).encode()

    @staticmethod
    def decode(s: bytes):
        asJson = json.loads(s.decode()[1:].strip("$"))
        return Machine(
            asJson["name"],
            asJson["host_ip"],
            asJson["port"],
            asJson["connections"],
        )


class Event(Wireable):
    """
    A class that monitors the types of messages sent in our system
    """

    @staticmethod
    def unique_char():
        return "e"

    def __init__(self, event_type: str, source: str, sink: str):
        self.event_type = event_type
        self.source = source
        self.sink = sink

    def __str__(self):
        return f"Event({self.event_type}, {self.source}, {self.sink})"

    def __eq__(self, other):
        if type(other) != Event:
            return False
        return str(self) == str(other)

    def encode(self):
        return f"{Event.unique_char()}{self.event_type}@{self.source}@{self.sink}{DELIM}".encode()

    @staticmethod
    def decode(s: bytes):
        data = (s.decode())[1:].split("@")
        return Event(data[0], data[1], data[2])


WIREABLE_CLASSES = [
    Ping,
    CommsRequest,
    CommsResponse,
    Vec2,
    Spell,
    Player,
    GameState,
    KeyInput,
    MouseInput,
    InputState,
    ConnectRequest,
    ConnectResponse,
    Machine,
    Event,
]


def wire_decode(s: bytes):
    arr = s.decode().split(DELIM)
    if len(arr) == 0:
        raise errors.InvalidMessage(f"Invalid message")
    s = arr[0].encode()
    if len(s) > 0:
        for cls in WIREABLE_CLASSES:
            if s.decode()[0] == cls.unique_char():
                return cls.decode(s)
    raise errors.InvalidMessage(f"Invalid message: {s}")

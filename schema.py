from game import consts
import math
import errors
import json


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
        return f"{Ping.unique_char()}".encode()

    @staticmethod
    def decode(_) -> "Ping":
        return Ping()


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
        return f"{Vec2.unique_char()}{data[0]}@{data[1]}".encode()

    @staticmethod
    def decode(s: bytes) -> "Vec2":
        data = (s.decode())[1:].split("@")
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

    def __init__(self, id: int, pos: Vec2, ivel: Vec2, creator: int):
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
        return f"{Spell.unique_char()}{data[0]}@{data[1]}@{data[2]}@{data[3]}@{data[4]}@{data[5]}".encode()

    @staticmethod
    def decode(s: bytes):
        data = (s.decode())[1:].split("@")
        return Spell(
            int(data[0]),
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
        return f"{Player.unique_char()}{data[0]}@{data[1]}@{data[2]}@{data[3]}@{data[4]}@{data[5]}@{data[6]}@{data[7]}@{data[8]}".encode()

    @staticmethod
    def decode(s: bytes):
        data = (s.decode())[1:].split("@")
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
        next_leader: str,
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
            player_encodings.append(str(player.encode())[2:-1])
        spell_encodings = []
        for spell in self.spells:
            spell_encodings.append(str(spell.encode())[2:-1])
        result = GameState.unique_char()
        result += f"{self.next_leader}"
        result += "#"
        result += f"{','.join(player_encodings)}"
        result += "#"
        result += f"{','.join(spell_encodings)}"
        result += "#"
        result += f"{self.spell_count}"
        return result.encode()

    @staticmethod
    def decode(s: bytes):
        data = (s.decode())[1:].split("#")
        next_leader = data[0]
        player_data = data[1].split(",")
        spell_data = data[2].split(",")
        players = []
        for player in player_data:
            players.append(Player.decode(player.encode()))
        spells = []
        for spell in spell_data:
            if len(spell) <= 0:
                continue
            spells.append(Spell.decode(spell.encode()))
        spell_count = int(data[3])
        return GameState(next_leader, players, spells, spell_count)


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
        return (
            f"{KeyInput.unique_char()}{data[0]}@{data[1]}@{data[2]}@{data[3]}".encode()
        )

    @staticmethod
    def decode(s: bytes):
        data = (s.decode())[1:].split("@")
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
        return f"{MouseInput.unique_char()}{data[0]}@{data[1]}@{data[2]}@{data[3]}@{data[4]}".encode()

    @staticmethod
    def decode(s: bytes):
        data = (s.decode())[1:].split("@")
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
        return f"{InputState.unique_char()}{self.key_input.encode().decode()}#{self.mouse_input.encode().decode()}".encode()

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

    def __init__(self, name: str, ip: str):
        self.name = name
        self.ip = ip

    def __str__(self):
        return f"ConnectRequest({self.name}, {self.ip})"

    def __eq__(self, other):
        if type(other) != ConnectRequest:
            return False
        return str(self) == str(other)

    def encode(self):
        return f"{ConnectRequest.unique_char()}{self.name}@{self.ip}".encode()

    @staticmethod
    def decode(s: bytes):
        data = (s.decode())[1:].split("@")
        return ConnectRequest(data[0], data[1])


class ConnectResponse(Wireable):
    """
    What the negotiator sends in response to a client connecting
    """

    @staticmethod
    def unique_char():
        return "r"

    def __init__(self, success: bool):
        self.success = success

    def __str__(self):
        return f"ConnectResponse({self.success})"

    def __eq__(self, other):
        if type(other) != ConnectResponse:
            return False
        return str(self) == str(other)

    def encode(self):
        return f"{ConnectResponse.unique_char()}{self.success}".encode()

    @staticmethod
    def decode(s: bytes):
        data = (s.decode())[1:]
        return ConnectResponse(data == "True")


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
        input_port: int,
        game_port: int,
        health_port: int,
        num_listens: int,
        connections: list[str],
    ) -> None:
        # The name of the machine
        self.name = name
        # The ip address the machine should listen on for new connections
        self.host_ip = host_ip
        # A dedicated port to just receive players input as it changes
        self.input_port = input_port
        # The most interesting port, where game state is sent and transitions can happen
        self.game_port = game_port
        # The port the machine should listen on for health checks
        self.health_port = health_port
        # The number of connections the machine should listen for
        self.num_listens = num_listens
        # The names of the machines that this machine should connect to
        self.connections = connections

    def __str__(self):
        return f"Machine({self.name}, {self.host_ip}, {self.input_port}, {self.game_port}, {self.health_port}, {self.num_listens}, {self.connections})"

    def __eq__(self, other):
        if type(other) != Machine:
            return False
        return str(self) == str(other)

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    def encode(self):
        return (self.unique_char() + self.toJson()).encode()

    @staticmethod
    def decode(s: bytes):
        asJson = json.loads(s.decode()[1:])
        return Machine(
            asJson["name"],
            asJson["host_ip"],
            asJson["input_port"],
            asJson["game_port"],
            asJson["health_port"],
            asJson["num_listens"],
            asJson["connections"],
        )


WIREABLE_CLASSES = [
    Ping,
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
]


def wire_decode(s: bytes):
    if len(s) > 0:
        for cls in WIREABLE_CLASSES:
            if s.decode()[0] == cls.unique_char():
                return cls.decode(s)
    raise errors.InvalidMessage(f"Invalid message: {s}")

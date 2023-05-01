from connections.machine import Machine

NEGOTIATOR_IP = "localhost"
NEGOTIATOR_PORT = 50051

# A null machine essentially
BLANK_MACHINE = Machine(
    name="",
    host_ip="",
    input_port=0,
    game_port=0,
    health_port=0,
    num_listens=0,
    connections=[],
)

"""

# Create the three identities that the machines can assume
MACHINE_A = Machine(
    name="A",
    host_ip="127.0.0.1",
    input_port=50051,
    game_port=50052,
    health_port=50053,
    num_listens=1,
    connections=[],
)

MACHINE_B = Machine(
    name="B",
    host_ip="127.0.0.1",
    input_port=50061,
    game_port=50062,
    health_port=50063,
    num_listens=0,
    connections=["A"],
)

# Create a mapping from machine name to information about it
MACHINE_MAP = {
    "A": MACHINE_A,
    "B": MACHINE_B,
}


def get_other_machines(name: str) -> list[Machine]:
    
    return [MACHINE_MAP[key] for key in MACHINE_MAP if key != name]
"""

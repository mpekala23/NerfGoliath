from connections.machine import Machine

# How players will connect to the game, through a coordinating server
NEGOTIATOR_IP = "127.0.0.1"
NEGOTIATOR_PORT = 50051

# How we will monitor stats about the game, through a passive "watching" server
WATCHER_IP = "127.0.0.1"
WATCHER_PORT = 50052

# Broadcasting state every tick is to much for the watcher to handle, so we throttle it
# by essentially choosing to monitor roughly every 20th tick (throw in some randomness)
TICKS_PER_WATCH = 30

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

# The minimum number of ticks that a machine must wait after becoming the leader before
# issuing a new leader change
LEADER_CHANGE_COOLDOWN = 60

ALIVE = 0
SUS = 1
DEAD = 2

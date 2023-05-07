SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Nerf Goliath"

# Controls stuff
RIGHT = 1
LEFT = 2
UP = 3
DOWN = 4


# Timing
RESPAWN_TIMER = 2


# Helper function to return the speed of the new projectile
def get_speed(diff):
    BASE = 1
    OFFSET = 1.5
    EXP = 3.75
    MAX_DIFF = 1
    diff = min(MAX_DIFF, diff)
    return BASE + (diff + OFFSET) ** EXP


# Stuff to prevent import circles
SPELL_LIVE_FOR = 500  # In milliseconds


DAVID_SCALING = 1.0
GOLIATH_SCALING = 2.0

NUM_PLAYERS = 5

FPS = 30

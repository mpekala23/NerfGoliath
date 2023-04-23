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
    OFFSET = 2
    EXP = 3
    MAX_DIFF = 1
    diff = min(MAX_DIFF, diff)
    return BASE + (diff + OFFSET) ** EXP

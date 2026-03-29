# Room dimensions (width, height) in tiles
BASE_ROOM_SIZE = (24, 9)  # Starting room size
ROOM_SIZE = (9, 9)        # Standard room size

# Hallway dimensions
HALL_LENGTH = 6      # Length of hallways in tiles
HALL_THICKNESS = 3   # Width/thickness of hallways in tiles

# Wall dimensions
WALL_HEIGHT = 2      # Height of wall prefabs in tiles

# Rendering settings
SCREEN_W = 1700
SCREEN_H = 900
TILE_SIZE_START = 4
TILE_SIZE_MIN = 1
TILE_SIZE_MAX = 40
CAMERA_SPEED = 18

# Default generation parameters
SIDE_START_CHANCE = 1.0
SIDE_DECAY = 0.01
BRANCH_FROM_SIDE_START_CHANCE = 1.0
BRANCH_FROM_SIDE_DECAY = 0.01
TOP_BOTTOM_START_CHANCE = 1.0
TOP_BOTTOM_DECAY = 0.01
BRANCH_FROM_TOP_BOTTOM_START_CHANCE = 1.0
BRANCH_FROM_TOP_BOTTOM_DECAY = 0.01
MIN_BRANCH_CHANCE = 0.0
MAX_BRANCHING_DEPTH = 100
GENERATE_VERTICAL_FIRST = False
ALLOW_HALLWAY_THROUGH_ROOMS = False

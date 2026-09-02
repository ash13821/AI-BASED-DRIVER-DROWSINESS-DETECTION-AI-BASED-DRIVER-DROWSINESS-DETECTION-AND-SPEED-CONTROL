"""
config.py

Central configuration for the AI-Based Drowsiness Prevention System -
Vehicle Simulation Module.

All tunable constants live here so behaviour can be adjusted without
touching the simulation, control, or UI logic.
"""

# ---------------------------------------------------------------------------
# SCREEN / WINDOW
# ---------------------------------------------------------------------------
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 720
FPS = 60
WINDOW_TITLE = "AI Vehicle Safety Simulation"

# ---------------------------------------------------------------------------
# ROAD
# ---------------------------------------------------------------------------
NUM_LANES = 2
ROAD_WIDTH = 380                       # total width of the road, in pixels
LANE_WIDTH = ROAD_WIDTH // NUM_LANES
ROAD_LEFT = (SCREEN_WIDTH - ROAD_WIDTH) // 2
ROAD_RIGHT = ROAD_LEFT + ROAD_WIDTH

DASH_LENGTH = 40                       # length of a single lane-marking dash
DASH_GAP = 30                          # gap between dashes
DASH_WIDTH = 6

ROAD_BOUNDARY_WIDTH = 6

# Conversion used to translate real-world speed into on-screen scroll speed.
# This purely controls how "fast" the road/obstacle appear to move; it does
# not represent a real physical scale.
PIXELS_PER_METER = 4.0

# ---------------------------------------------------------------------------
# SPEEDS (km/h)
# ---------------------------------------------------------------------------
NORMAL_SPEED = 80          # target speed while driver is AWAKE
SAFE_SPEED = 40            # target speed while driver is DROWSY
MIN_SPEED = 0
MAX_SPEED = 120

# ---------------------------------------------------------------------------
# ACCELERATION / DECELERATION RATES (km/h per second)
# ---------------------------------------------------------------------------
ACCELERATION = 12.0                # rate of speeding back up towards normal
DECELERATION = 15.0                # rate of gradual drowsiness slowdown
EMERGENCY_DECELERATION = 45.0      # rate of hard braking

# ---------------------------------------------------------------------------
# OBSTACLE / DISTANCE (meters)
# ---------------------------------------------------------------------------
INITIAL_OBSTACLE_DISTANCE = 90.0
MIN_OBSTACLE_DISTANCE = 3.0
MAX_OBSTACLE_DISTANCE = 140.0
RESPAWN_DISTANCE = 120.0           # distance obstacle resets to once it is far ahead

SAFE_DISTANCE = 40.0               # distance considered "safe" for normal driving
EMERGENCY_DISTANCE = 18.0          # below this -> emergency braking, regardless of driver state

OBSTACLE_BASE_SPEED = 70.0         # km/h - normal cruising speed of the vehicle ahead
OBSTACLE_EVENT_SPEED_FACTOR = 0.15 # how much the obstacle slows during a triggered braking event
OBSTACLE_EVENT_DURATION = 3.5      # seconds the obstacle braking event lasts

# ---------------------------------------------------------------------------
# DRIVER STATES
# ---------------------------------------------------------------------------
STATE_AWAKE = "AWAKE"
STATE_DROWSY = "DROWSY"

# ---------------------------------------------------------------------------
# CONTROLLER STATES
# ---------------------------------------------------------------------------
NORMAL_DRIVING = "NORMAL_DRIVING"
DROWSINESS_SLOWDOWN = "DROWSINESS_SLOWDOWN"
EMERGENCY_BRAKING = "EMERGENCY_BRAKING"

# ---------------------------------------------------------------------------
# CONTROL OUTPUT (what would eventually be sent to simulation OR hardware)
# ---------------------------------------------------------------------------
CONTROL_NORMAL = "NORMAL"
CONTROL_SLOW_DOWN = "SLOW_DOWN"
CONTROL_EMERGENCY_BRAKE = "EMERGENCY_BRAKE"

# ---------------------------------------------------------------------------
# BRAKE STATUS LABELS
# ---------------------------------------------------------------------------
BRAKE_OFF = "OFF"
BRAKE_ACTIVE = "ACTIVE"
BRAKE_EMERGENCY = "EMERGENCY"

# ---------------------------------------------------------------------------
# COLORS (R, G, B)
# ---------------------------------------------------------------------------
COLOR_BACKGROUND = (34, 92, 51)        # grass
COLOR_ROAD = (48, 48, 52)
COLOR_ROAD_BOUNDARY = (235, 235, 235)
COLOR_LANE_MARKING = (240, 200, 40)

COLOR_PLAYER_VEHICLE = (40, 130, 240)  # blue
COLOR_OBSTACLE_VEHICLE = (200, 40, 40) # red

COLOR_PANEL_BG = (18, 18, 22)
COLOR_TEXT = (235, 235, 235)
COLOR_TEXT_DIM = (170, 170, 170)
COLOR_GOOD = (70, 220, 90)
COLOR_WARNING = (250, 190, 40)
COLOR_DANGER = (240, 60, 60)

# ---------------------------------------------------------------------------
# VEHICLE DIMENSIONS (pixels)
# ---------------------------------------------------------------------------
PLAYER_VEHICLE_WIDTH = 46
PLAYER_VEHICLE_HEIGHT = 78
OBSTACLE_VEHICLE_WIDTH = 46
OBSTACLE_VEHICLE_HEIGHT = 78

PLAYER_SCREEN_Y = SCREEN_HEIGHT - 150   # fixed vertical position of the player's car

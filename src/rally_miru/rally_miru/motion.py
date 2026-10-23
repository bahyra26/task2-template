import math

from rally_interfaces.msg import Instruction

CELL_SIZE = 1.0  # [m]
GRID_OFFSET = 1.0  # [m] pusat kotak (0, 0) ada di koordinat (1, 1)

TURN_TOLERANCE = 0.01  # [rad] belokan dianggap selesai jika sisa putarannya lebih kecil dari ini
MAX_TURN_RATE = 1.5  # [rad/s]
MIN_TURN_RATE = 0.3  # [rad/s]
TURN_GAIN = 4.0  # [1/s]


# Provided, do not modify
def wrap_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))

def snap_to_cell_center(value):
    return round((value - GRID_OFFSET) / CELL_SIZE) * CELL_SIZE + GRID_OFFSET

def snap_heading(theta):
    return wrap_angle(round(theta / (math.pi / 2)) * (math.pi / 2))

# TODO: TASK D
def target_point(x, y, heading, cells):
    distance = cells * CELL_SIZE
    return x + distance * math.cos(heading), y + distance * math.sin(heading)  
    # Hitung titik tujuan jika maju `cells` kotak dari (x, y) searah `heading`. Return (target_x,
    # target_y).

def remaining_distance(x, y, heading, target_x, target_y):
    return (target_x - x) * math.cos(heading) + (target_y - y) * math.sin(heading) 
    # Hitung sisa jarak ke titik tujuan searah `heading`.

# TODO: TASK E
def turn_target(heading, turn):
    if turn == Instruction.TURN_LEFT:
        heading += math.pi / 2
    elif turn == Instruction.TURN_RIGHT:
        heading -= math.pi / 2 
    # Hitung arah setelah belok 90 derajat dari `heading` (kiri menambah sudut, kanan mengurangi),
    # lalu rapikan dengan wrap_angle.
    return wrap_angle(heading)

# Provided, do not modify
def turn_rate(error):
    if abs(error) < TURN_TOLERANCE:
        return 0.0

    rate = min(MAX_TURN_RATE, max(MIN_TURN_RATE, abs(error) * TURN_GAIN))
    return math.copysign(rate, error)

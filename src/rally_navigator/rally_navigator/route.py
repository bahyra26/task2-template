from collections import deque

from rally_interfaces.msg import Instruction
from rally_navigator.grid import Cell, DIRECTION_COL, DIRECTION_COUNT, DIRECTION_ROW, EAST

# Provided, do not modify.
def trace_back(parent, finish):
    if finish not in parent:
        return []

    route = []
    cell = finish
    while cell is not None:
        route.append(cell)
        cell = parent[cell]
    route.reverse()
    return route

# TODO: TASK B
def find_route(grid):
    if not grid.inside(grid.start) or not grid.inside(grid.finish):
        return []

    parent = {grid.start: None}
    pending = deque([grid.start])

    while pending:
        current = pending.popleft()
        if current == grid.finish:
            break

        # Urutan tetangga: timur (0), utara (1), barat (2), selatan (3) sesuai DIRECTION_COL/ROW
        for i in range(DIRECTION_COUNT):
            next_cell = Cell(current.col + DIRECTION_COL[i], current.row + DIRECTION_ROW[i])
            if grid.inside(next_cell) and not grid.is_rock(next_cell) and next_cell not in parent:
                parent[next_cell] = current
                pending.append(next_cell)

    return trace_back(parent, grid.finish)

# TODO: TASK C
def route_to_directions(route):
    """
    Ubah rute (daftar kotak) jadi daftar arah tiap langkah: 0 timur, 1 utara, 2 barat, 3 selatan.
    """
    directions = []
    for i in range(len(route) - 1):
        c1, r1 = route[i]
        c2, r2 = route[i + 1]
        dc = c2 - c1
        dr = r2 - r1
        for d in range(DIRECTION_COUNT):
            if DIRECTION_COL[d] == dc and DIRECTION_ROW[d] == dr:
                directions.append(d)
                break
    return directions

# TODO: TASK D
def directions_to_instructions(directions):
    if not directions:
        msg = Instruction()
        msg.id = 1
        msg.distance = 0
        msg.turn = Instruction.TURN_NONE
        return [msg]

    raw_instructions = []
    current_heading = EAST  # 0 (timur)

    # Langkah pertama bukan ke timur: belok dulu, jarak 0
    first_dir = directions[0]
    if first_dir != current_heading:
        diff = (first_dir - current_heading) % DIRECTION_COUNT
        if diff == 1:
            raw_instructions.append((0, Instruction.TURN_LEFT))
        elif diff == 3:
            raw_instructions.append((0, Instruction.TURN_RIGHT))
        elif diff == 2:
            raw_instructions.append((0, Instruction.TURN_LEFT))
            raw_instructions.append((0, Instruction.TURN_LEFT))
        current_heading = first_dir

    i = 0
    n = len(directions)
    while i < n:
        dist = 0
        while i < n and directions[i] == current_heading:
            dist += 1
            i += 1

        if i >= n:
            raw_instructions.append((dist, Instruction.TURN_NONE))
            break

        next_dir = directions[i]
        diff = (next_dir - current_heading) % DIRECTION_COUNT

        if diff == 1:
            raw_instructions.append((dist, Instruction.TURN_LEFT))
            current_heading = next_dir
        elif diff == 3:
            raw_instructions.append((dist, Instruction.TURN_RIGHT))
            current_heading = next_dir
        elif diff == 2:
            # Putar balik 180° ditulis dua belok kiri berturut-turut, yang kedua jaraknya 0
            raw_instructions.append((dist, Instruction.TURN_LEFT))
            raw_instructions.append((0, Instruction.TURN_LEFT))
            current_heading = next_dir

    # Konversi ke objek pesan ROS Instruction dengan id mulai dari 1
    instructions = []
    for idx, (dist, turn) in enumerate(raw_instructions, start=1):
        msg = Instruction()
        msg.id = idx
        msg.distance = dist
        msg.turn = turn
        instructions.append(msg)

    return instructions

# Provided, do not modify
def route_to_instructions(route):
    return directions_to_instructions(route_to_directions(route))

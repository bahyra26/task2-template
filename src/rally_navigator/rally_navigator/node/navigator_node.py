from rally_interfaces.msg import DriverStatus, Instruction, RaceMap
from rally_navigator.grid import Cell, GridMap
from rally_navigator.route import find_route, route_to_instructions
from rcl_interfaces.msg import SetParametersResult
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy

MAP_TOPIC = '/race/map'
STATUS_TOPIC = '/miru/status'
INSTRUCTION_TOPIC = '/navigator/instruction'
INSTRUCTIONS_AHEAD_PARAM = 'instructions_ahead'

DEFAULT_INSTRUCTIONS_AHEAD = 2
MIN_INSTRUCTIONS_AHEAD = 1
MAX_INSTRUCTIONS_AHEAD = 5

TURN_NAMES = {
    Instruction.TURN_NONE: 'finish',
    Instruction.TURN_LEFT: 'belok kiri',
    Instruction.TURN_RIGHT: 'belok kanan',
}

class NavigatorNode:
    def __init__(self, node):
        self.node = node

        self.grid = None
        self.instructions = []
        self.last_status = None
        self.sent_count = 0

        # [TASK A] Subscribe ke MAP_TOPIC dengan QoS transient_local dan reliable
        map_qos = QoSProfile(
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE,
            depth=1
        )
        self.map_subscription = self.node.create_subscription(
            RaceMap, MAP_TOPIC, self.on_map, map_qos
        )

        # [TASK E] Buat publisher untuk INSTRUCTION_TOPIC dan subscriber untuk STATUS_TOPIC
        self.instruction_publisher = self.node.create_publisher(Instruction, INSTRUCTION_TOPIC, 10)
        self.status_subscription = self.node.create_subscription(
            DriverStatus, STATUS_TOPIC, self.on_status, 10
        )

        # [TASK F] Daftarkan parameter INSTRUCTIONS_AHEAD_PARAM dengan nilai bawaan dan callback
        self.node.declare_parameter(INSTRUCTIONS_AHEAD_PARAM, DEFAULT_INSTRUCTIONS_AHEAD)
        self.node.add_on_set_parameters_callback(self.on_parameter_change)

        self.node.get_logger().info('navigator siap')

    # [TASK A] Callback penerimaan peta
    def on_map(self, msg):
        if self.grid is not None:
            return  # Abaikan peta kedua

        if len(msg.rocks) != msg.width * msg.height:
            self.node.error('jumlah batu tidak cocok dengan ukuran peta')
            return

        start = Cell(msg.start_col, msg.start_row)
        finish = Cell(msg.finish_col, msg.finish_row)
        self.grid = GridMap(msg.width, msg.height, msg.rocks, start, finish)

        rock_count = sum(msg.rocks)
        self.node.get_logger().info(
            f'[navigator] peta diterima: {msg.width}x{msg.height}, {rock_count} batu, start ({msg.start_col}, {msg.start_row}), finis ({msg.finish_col}, {msg.finish_row})'
        )
        self.plan_route()

    # Provided, do not modify
    def plan_route(self):
        route = find_route(self.grid)
        if not route:
            self.node.get_logger().error('tidak ada rute dari start ke finish')
            return

        self.instructions = route_to_instructions(route)
        self.node.get_logger().info(
            f'rute {len(route) - 1} kotak, {len(self.instructions)} instruksi')
        
        if self.last_status is not None:
            self.send_instructions()

    # [TASK E] Callback status dari Miru
    def on_status(self, msg):
        self.last_status = msg
        self.send_instructions()

    def send_instructions(self):
        # Jangan kirim jika rute belum ada, Miru belum lapor, atau belum ada subscriber
        if not self.instructions or self.last_status is None:
            return
        if self.instruction_publisher.get_subscription_count() == 0:
            return

        instructions_ahead = self.node.get_parameter(INSTRUCTIONS_AHEAD_PARAM).value
        done_id = self.last_status.done_id
        target_max_id = done_id + instructions_ahead

        while self.sent_count < len(self.instructions) and self.sent_count < target_max_id:
            # Ambil langsung objek Instruction dari list tanpa unpacking tuple
            msg = self.instructions[self.sent_count]
            inst_id = msg.id
            dist = msg.distance
            turn = msg.turn

            self.instruction_publisher.publish(msg)

            turn_desc = TURN_NAMES.get(turn, 'unknown')
            self.node.get_logger().info(
                f'[navigator] kirim instruksi {inst_id}: jarak {dist}, {turn_desc}'
            )
            self.sent_count += 1

    # [TASK F] Validasi perubahan parameter instructions_ahead
    def on_parameter_change(self, parameters):
        for param in parameters:
            if param.name == INSTRUCTIONS_AHEAD_PARAM:
                val = param.value
                if not isinstance(val, int) or val < MIN_INSTRUCTIONS_AHEAD or val > MAX_INSTRUCTIONS_AHEAD:
                    return SetParametersResult(successful=False, reason=f'Nilai harus antara {MIN_INSTRUCTIONS_AHEAD} dan {MAX_INSTRUCTIONS_AHEAD}')
        
        res = SetParametersResult(successful=True)
        if self.instructions and self.last_status is not None:
            self.send_instructions()
        return res

import pymunk
from enum import Enum
from math import copysign

class Direction(Enum):
    UP = 0b0001
    DOWN = 0b0010
    LEFT = 0b0100
    RIGHT = 0b1000

    @staticmethod
    def mask(num):
        return (
            Direction.UP.value | Direction.DOWN.value | Direction.LEFT.value
            | Direction.RIGHT.value
        ) & num

    @staticmethod
    def check(num, variant):
        return (Direction.mask(num) & variant.value) == variant.value

    @staticmethod
    def get(input):
        input = input.upper()
        if input == "UP":
            return Direction.UP
        elif input == "DOWN":
            return Direction.DOWN
        elif input == "LEFT":
            return Direction.LEFT
        elif input == "RIGHT":
            return Direction.RIGHT
        else:
            raise ValueError("Input ({}) did not match any variant of Direction".format(input))

class KeyAction(Enum):
    PRESSED = 0b0_0000
    RELEASED = 0b1_0000

    @staticmethod
    def mask(num):
        return (KeyAction.PRESSED.value | KeyAction.RELEASED.value) & num

    @staticmethod
    def get(input):
        input = input.upper()
        if input == "PRESSED":
            return KeyAction.PRESSED
        elif input == "RELEASED":
            return KeyAction.RELEASED
        else:
            raise ValueError("Input ({}) did not match any variant of KeyAction".format(input))

class EntityType(Enum):
    NORMAL_PLAYER = 1
    ZOMBIE_PLAYER = 2
    GOD_PLAYER = 4

    @staticmethod
    def mask(num):
        return (EntityType.NORMAL_PLAYER.value | EntityType.ZOMBIE_PLAYER.value | EntityType.GOD.value) & num

class Game:
    MAX_VELOCITY = 5
    ACCELERATION = 1
    INTERNAL_TICK_TIME = 0.01
    EXTERNAL_TICK_TIME = 0.01
    MAX_TICKS = 600

    def __init__(self, width=800.0, height=1200.0):

        self.starting_positions = [(-100, 0), (0, -100), (10, 0), (50, 0), (50, 50), (-50, -50),
                                   (-50, 0), (0, -50), (0, 40), (100, 100)]
        self.players = dict()
        self.width = width
        self.height = height
        self.space = pymunk.Space()
        self.add_static_scenery()
        self.zombie_collision_handler = self.space.add_collision_handler(
            EntityType.NORMAL_PLAYER.value, EntityType.ZOMBIE_PLAYER.value
        )
        self.running = False
        self.tick_count = 0
        self.god = None

        def turn_zombie(arbiter, space, data):
            player = self.players[arbiter.shapes[0].id]
            player.shape.collision_type = EntityType.ZOMBIE_PLAYER.value

            return True

        self.zombie_collision_handler.begin = turn_zombie
        self.space.damping = 0.1

    def is_ended_with_winner(self):
        zombie_win_condition = not any(
            player.shape.collision_type == EntityType.NORMAL_PLAYER.value
            for player in self.players.values()
        )
        player_win_condition = self.tick_count > Game.MAX_TICKS
        if zombie_win_condition and len(self.player) > 0:
            return True, EntityType.ZOMBIE_PLAYER.value
        elif player_win_condition:
            return True, EntityType.NORMAL_PLAYER.value
        else:
            return False, None

    def add_player(self, id):
        self.players[id] = Player(id, self.space, self.starting_positions.pop())

    def add_god(self, id):
        if self.god is None:
            self.god = God(id)
            self.players[id] = self.god
        else:
            self.players[id] = Player(id, self.space, self.starting_positions.pop())

    def add_static_scenery(self):
        static_body = self.space.static_body
        static_lines = [
            pymunk.Segment(
                static_body, (self.width / 2, self.height / 2), (self.width / 2, -self.height / 2),
                0.0
            ),
            pymunk.Segment(
                static_body, (self.width / 2, -self.height / 2),
                (-self.width / 2, -self.height / 2), 0.0
            ),
            pymunk.Segment(
                static_body, (-self.width / 2, -self.height / 2),
                (-self.width / 2, self.height / 2), 0.0
            ),
            pymunk.Segment(
                static_body, (-self.width / 2, self.height / 2), (self.width / 2, self.height / 2),
                0.0
            )
        ]

        for line in static_lines:
            line.elasticity = 0.95
            line.friction = 0.9
        self.space.add(static_lines)

    def input(self, id, key, action):
        self.players[id].apply_input(key, action)

    def collect_render_data(self):
        data = dict()
        for player in self.players.items():
            self.space.reindex_shapes_for_body(player[1].body)
            data[player[0]] = dict(
                position=dict(
                    x=float(player[1].body.position[0]), y=float(player[1].body.position[1])
                ),
                isZombie=bool(player[1].shape.collision_type == EntityType.ZOMBIE_PLAYER.value)
            )

        return data

    def tick(self):
        if not self.running:
            return None, True, None

        self.tick_count += 1
        self.space.step(Game.INTERNAL_TICK_TIME)
        data = self.collect_render_data()

        game_over, winner = self.is_ended_with_winner()
        if game_over:
            self.running = False
            return data, True, winner
        else:
            return data, False, None

    def start(self):
        self.running = True

class Player:
    RADIUS = 25

    def __init__(self, id, space, pos):
        self.id = id
        self.body = pymunk.Body(1)
        self.space = space
        self.body.position = pos
        self.shape = pymunk.Circle(self.body, Player.RADIUS)
        self.shape.density = 3
        self.space.add(self.body, self.shape)
        self.shape.collision_type = EntityType.NORMAL_PLAYER.value
        self.current_accel_dirs = 0
        self.shape.id = id

        def velocity_cb(body, gravity, damping, dt):
            velocity_vector = [body.velocity[0], body.velocity[1]]

            if Direction.check(self.current_accel_dirs, Direction.RIGHT):
                body.velocity = 600, 0
            if Direction.check(self.current_accel_dirs, Direction.LEFT):
                body.velocity = -600, 0
            if Direction.check(self.current_accel_dirs, Direction.UP):
                body.velocity = 0, 600
            if Direction.check(self.current_accel_dirs, Direction.DOWN):
                body.velocity = 0, -600

        self.body.velocity_func = velocity_cb

    def apply_input(self, key, action):
        if action == KeyAction.PRESSED:
            self.current_accel_dirs |= key.value
        elif action == KeyAction.RELEASED:
            self.current_accel_dirs &= ~key.value
        else:
            raise TypeError("'action' param was not of KeyAction type", action)
class God:
    def __init__(self, id):
        self.id = id
        self.current_actions = [GodAction(GodAction.FREEZE, )]
        self.possible_actions = []
        self.cooldown_actions = []


class GodAction:
    FREEZE = 1
    SPEED_UP = 2
    IMMUNE = 3
    def __init__(self, id, data, duration, cooldown):
        self.data = data
        self.duration = duration
        self.cooldown = cooldown

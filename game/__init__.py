import pymunk

class Game:
    TYPES = {"player": 1, "zombie": 2}
    CONTROL = {
        "w_pressed": 1,
        "w_released": 5,
        "a_pressed": 2,
        "a_released": 6,
        "s_pressed": 3,
        "s_released": 7,
        "d_pressed": 4,
        "d_released": 8
    }
    MAX_VELOCITY = 5
    ACCELERATION = 1
    TICK_TIME = .1

    def __init__(self, width=5000.0, height=5000.0):

        self.starting_positions = [(-100, 0), (0, -100), (10, 0), (50, 0), (50, 50), (-50, -50),
                                   (-50, 0), (0, -50), (0, 40), (0, 10)]
        self.players = dict()
        self.width = width
        self.height = height
        self.space = pymunk.Space()
        self.add_static_scenery()
        self.zombie_collision_handler = self.space.add_collision_handler(
            Game.TYPES["player"], Game.TYPES["zombie"]
        )
        self.started = False
        self.ended = False

        def turn_zombie(arbiter, space, data):
            print("here")
            player = self.players[arbiter.shapes[0].id]
            player.shape.collision_type = Game.TYPES["zombie"]
            ended = True
            for player in self.players.values():
                if player.shape.collision_type == Game.TYPES["player"]:
                    ended = False
            self.ended = ended
            return True

        self.zombie_collision_handler.begin = turn_zombie
        self.space.damping = 0.1

    def add_player(self, id):
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

    def input(self, id, action):
        if Game.CONTROL[action] <= 4:
            self.players[id].current_accel_dirs.add(action[0])
        else:
            self.players[id].current_accel_dirs.remove(action[0])

    # [playerId:{position:point, velocity:point, isZombie:bool}]
    def tick(self):
        self.space.step(Game.TICK_TIME)
        data = dict()
        for player in self.players.items():
            data[player[0]] = dict()
            data[player[0]]["position"] = dict()
            data[player[0]]["position"].x = player[1].body.position[0]
            data[player[0]]["position"].y = player[1].body.position[1]
            self.space.reindex_shapes_for_body(player[1].body)
            data[player[0]]["isZombie"] = player[1].shape.collision_type == Game.TYPES["zombie"]
        return data, self.ended

    def start(self):
        self.started = True
        self.players[1].shape.collision_type = Game.types["zombie"]
        return {"width": self.width, "height": self.height, "player_radius": Player.radius}
class Player:
    radius = 25
    def __init__(self, id, space, pos):
        self.id = id
        self.body = pymunk.Body(1)
        self.space = space
        self.body.position = pos
        self.shape = pymunk.Circle(self.body, Player.radius)
        self.shape.density = 3
        self.space.add(self.body, self.shape)
        self.shape.collision_type = Game.TYPES["player"]
        self.current_accel_dirs = set()
        self.shape.id = id

        def velocity_cb(body, gravity, damping, dt):
            velocity_vector = [0, 0]
            if body.velocity[0] < Game.MAX_VELOCITY and "d" in self.current_accel_dirs:
                velocity_vector[0] = min(Game.MAX_VELOCITY, body.velocity[0] + Game.ACCELERATION)
            if body.velocity[0] > -Game.MAX_VELOCITY and "a" in self.current_accel_dirs:
                velocity_vector[0] = max(-Game.MAX_VELOCITY, body.velocity[0] - Game.ACCELERATION)
            if body.velocity[1] < Game.MAX_VELOCITY and "w" in self.current_accel_dirs:
                velocity_vector[1] = min(Game.MAX_VELOCITY, body.velocity[1] + Game.ACCELERATION)
            if body.velocity[1] > -Game.MAX_VELOCITY and "s" in self.current_accel_dirs:
                velocity_vector[1] = max(-Game.MAX_VELOCITY, body.velocity[1] - Game.ACCELERATION)
            body.velocity = velocity_vector

        self.body.velocity_func = velocity_cb

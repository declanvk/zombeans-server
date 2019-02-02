import pymunk


class Game:

    types = {"player": 1, "zombie": 2}
    control = {"w_pressed":1, "w_released":5, "a_pressed":2,
               "a_released":6, "s_pressed":3, "s_released":7,
               "d_pressed":4, "d_released":8}
    max_velocity = 5
    acceleration = .3
    friction = .3
    tick_time = .1

    def __init__(self, max_players = 8, min_players = 4, width = 500, height = 500):

        self.action_buffer = dict()
        self.max_players = max_players
        self.min_players = min_players
        self.players = dict()
        self.width = self.width
        self.height = self.height
        self.space = pymunk.Space()
        self.border = pymunk.Poly(self.space.static_body,  [(width/2, height/2),
                                                            (-width/2, height/2),
                                                            (-width/2, -height/2),
                                                            (width/2,-height/2)])
        self.space.add(self.border)
        self.zombie_collision_handler = self.space.add_collision_handler(Game.types["player"], Game.types["zombie"])

        def turn_zombie(arbiter, space, data):
            player = data[arbiter.shapes[0].id]
            player.type = Game.types["zombie"]
            return True

        self.zombie_collision_handler.begin = turn_zombie
        self.space.damping = 0.1


    def add_player(self, id):
        self.players[id] = Player(id)
        self.space.add(self.players[id].body, self.players[id].shape)

    def input(self, id, action):
        if Game.control[action] <= 4:
            self.players[id].current_accel_dirs.add(action[0])
        else:
            self.players[id].current_accel_dirs.remove(action[0])

    # [playerId:{position:point, velocity:point, isZombie:bool}]
    def tick(self):
        self.space.step(Game.tick_time)
        data = dict()
        for player in self.players:
            data[player] = dict
            data[player]["position"] = player.body.position
            data[player]["isZombie"] = player.type == Game.types["zombie"]
        return data


    def game_start(self):
        for x in self.players.items():
            self.zombie_collision_handler.data[x[0]] = x[1]


class Player:

    def __init__(self, id):
        self.id = id
        self.body = pymunk.Body()
        self.type = Game.types["player"]
        self.shape = pymunk.Circle(self.body)
        self.shape.collision_type = Game.types["player"]
        self.current_accel_dirs = set()
        self.shape.id = id

        def velocity_cb(body, gravity, damping, dt):
            if body.velocity[0] < Game.max_velocity and "d" in self.current_accel_dirs:
                body.velocity[0] += min(Game.max_velocity, body.velocity[0] + Game.acceleration)
            if body.velocity[0] > -Game.max_velocity and "a" in self.current_accel_dirs:
                body.velocity[0] = max(-Game.max_velocity, body.velocity[0]-Game.acceleration)
            if body.velocity[1] < Game.max_velocity and "w" in self.current_accel_dirs:
                body.velocity[1] += min(Game.max_velocity, body.velocity[1]+Game.acceleration)
            if body.velocity[1] > -Game.max_velocity and "s" in self.current_accel_dirs:
                body.velocity[1] = max(-Game.max_velocity, body.velocity[1]-Game.acceleration)


        self.body.velocity_func = velocity_cb





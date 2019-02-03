import pymunk
from enum import Enum
class Game:

    types = {"player": 1, "zombie": 2}
    MAX_VELOCITY = 100
    ACCELERATION = 1
    INTERNAL_TICK_TIME = 0.01
    EXTERNAL_TICK_TIME = 0.01
    MAX_TICKS = 60

    def __init__(self, max_players = 8, min_players = 4, width = 1300.0, height = 700.0):

        self.starting_positions = [(-100, 0), (0, -100), (10, 0), (50, 0),
                                   (50, 50), (-50, -50), (700, 100), (100, 300),
                                   (500, 500), (100, 100)]
        self.max_players = max_players
        self.min_players = min_players
        self.players = dict()
        self.width = width
        self.height = height
        self.space = pymunk.Space()
        self.add_static_scenery()
        self.zombie_collision_handler = self.space.add_collision_handler(Game.types["player"], Game.types["zombie"])
        self.started = False
        self.ended = False
        self.winner = None
        self.space.damping = 0.3
        self.god = None
        self.time_left = Game.MAX_TICKS
        self.effects = set()
        self.player_count = 0

        def turn_zombie(arbiter, space, data):
            if self.god is not None and GodAction.IMMUNE in self.god.current_actions:
                return True

            player = self.players[arbiter.shapes[0].id]
            player.shape.collision_type = Game.types["zombie"]
            ended = True
            for player in self.players.values():
                if player.shape.collision_type == Game.types["player"]:
                    ended = False
            self.ended = ended
            if ended:
                self.winner = Game.types["zombie"]
            return True

        self.zombie_collision_handler.begin = turn_zombie
        self.space.damping = 0.1

    def add_player(self, id):
        print(id + "connected")
        print(self.player_count)
        if self.player_count == 0:
            self.players[id] = Player(id, self.space, self.starting_positions.pop(), self, isZombie=True)
        elif self.player_count == 1 and self.god is None:
            self.add_god(id)
        else:
            self.players[id] = Player(id, self.space, self.starting_positions.pop(), self)
        self.player_count += 1

    def add_god(self, id):
        self.god = God(id)

    def add_static_scenery(self):
        static_body = self.space.static_body
        static_lines = [pymunk.Segment(static_body, (0,0),
                                       (self.width, 0), 0.0),
                        pymunk.Segment(static_body, (self.width, 0),
                                       (self.width, self.height), 0.0),
                        pymunk.Segment(static_body, (self.width, self.height),
                                       (0, self.height), 0.0),
                        pymunk.Segment(static_body, (0, self.height),
                                       (0, 0), 0.0)]
        for line in static_lines:
            line.elasticity = 0.95
            line.friction = 0.9
        self.space.add(static_lines)

    def input(self, id, key, action):
        if action == "pressed":
            self.players[id].current_accel_dirs.add(key[0])
        else:
            self.players[id].current_accel_dirs.remove(key[0])

    def god_input(self, id, code):
        if self.god is not None and id == self.god.id:
            if code in self.god.possible_actions:
                self.god.current_actions[code] = self.god.possible_actions[code]
                self.god.cooldown_actions[code] = self.god.possible_actions[code]
                self.god.possible_actions.remove(code)

    def cure_player(self):
        for obj in self.players.values():
            if obj.shape.collision_type == Game.types["zombie"]:
                obj.shape.collision_type = Game.types["player"]
    # [playerId:{position:point, velocity:point, isZombie:bool}]

    def tick(self):
        self.space.step(Game.INTERNAL_TICK_TIME)
        if self.god is not None and GodAction.CURE in self.god.current_actions:
            self.cure_player()
        self.time_left -= Game.INTERNAL_TICK_TIME
        if self.god is not None:
            self.god.tick()
        if self.time_left <= 0:
            self.ended = True
            self.winner = Game.types["player"]
        data = dict()
        for player in self.players.items():
            data[player[0]] = dict()
            data[player[0]]["position"] = dict()
            data[player[0]]["position"]["x"] = player[1].body.position[0]
            data[player[0]]["position"]["y"] = player[1].body.position[1]
            self.space.reindex_shapes_for_body(player[1].body)
            data[player[0]]["isZombie"] = player[1].shape.collision_type == Game.types["zombie"]
        if self.god is not None:
            data["god_spells"] = {"possible": list(self.god.possible_actions.keys()),
                                  "cooldown": {x.id : x.cooldown for x in self.god.cooldown_actions.values()}
                                 }
        return data, self.ended, self.winner


    def start(self):
        self.started = True
        return {"width": self.width, "height": self.height}


class Player:
    RADIUS = 60.0

    def __init__(self, id, space, pos, game, isZombie=False):
        self.id = id
        self.body = pymunk.Body(1)
        self.space = space
        self.body.position = pos
        self.shape = pymunk.Circle(self.body, Player.RADIUS)
        self.shape.density = 3
        self.space.add(self.body, self.shape)
        self.shape.collision_type = Game.types["player"]
        if isZombie:
            self.shape.collision_type = Game.types["zombie"]
        else:
            self.shape.collision_type = Game.types["player"]
        self.current_accel_dirs = set()
        self.shape.id = id
        self.game = game

        def velocity_cb(body, gravity, damping, dt):
            velocity_vector = [body.velocity[0], body.velocity[1]]
            accel_modifier = 1
            max_vel_mod = 1
            if self.shape.collision_type == Game.types["zombie"] and \
                self.game.god is not None and GodAction.FREEZE in self.game.god.current_actions:
                body.velocity = [0, 0]
            if self.shape.collision_type == Game.types["player"] and \
                self.game.god is not None and \
                GodAction.SPEED_UP in self.game.god.current_actions:
                accel_modifier = 1.5
                max_vel_mod = 2

            if body.velocity[0] < Game.MAX_VELOCITY * max_vel_mod and "r" in self.current_accel_dirs:
                velocity_vector[0] = min(Game.MAX_VELOCITY * max_vel_mod, body.velocity[0] + Game.ACCELERATION * accel_modifier )
            if body.velocity[0] > -Game.MAX_VELOCITY * max_vel_mod and "l" in self.current_accel_dirs:
                velocity_vector[0] = max(-Game.MAX_VELOCITY * max_vel_mod, body.velocity[0]-Game.ACCELERATION * accel_modifier)
            if body.velocity[1] < Game.MAX_VELOCITY * max_vel_mod and "d" in self.current_accel_dirs:
                velocity_vector[1] = min(Game.MAX_VELOCITY * max_vel_mod, body.velocity[1]+Game.ACCELERATION * accel_modifier)
            if body.velocity[1] > -Game.MAX_VELOCITY * max_vel_mod and "u" in self.current_accel_dirs:
                velocity_vector[1] = max(-Game.MAX_VELOCITY * max_vel_mod, body.velocity[1]-Game.ACCELERATION * accel_modifier)
            body.velocity = velocity_vector

        self.body.velocity_func = velocity_cb

class God:
    def __init__(self, id):
        self.id = id
        self.current_actions = dict()
        self.possible_actions = {GodAction.FREEZE: GodAction(GodAction.FREEZE, 3, 40),
                                 GodAction.SPEED_UP: GodAction(GodAction.SPEED_UP, 2, 10),
                                 GodAction.IMMUNE: GodAction(GodAction.IMMUNE, 2, 20)}
        self.cooldown_actions = {GodAction.CURE: GodAction(GodAction.CURE, 0, 30)}

    def tick(self):
        to_splice = set()
        for (act, obj) in self.cooldown_actions.items():
            obj.cooldown -= Game.INTERNAL_TICK_TIME
            if obj.cooldown <= 0:
                to_splice.add(act)
                self.possible_actions[act] = obj
                obj.cooldown = obj.full_cooldown
        for i in to_splice:
            self.cooldown_actions.pop(i)

        to_splice = set()
        for (act, obj) in self.current_actions.items():
            obj.duration -= Game.INTERNAL_TICK_TIME
            if obj.duration <= 0:
                to_splice.add(act)
                self.cooldown_actions[act] = obj
                obj.duration = obj.full_duration
        for i in to_splice:
            self.current_actions.pop(i)





class GodAction:
    FREEZE = 1
    SPEED_UP = 2
    IMMUNE = 3
    CURE = 4
    def __init__(self, id, duration, cooldown):
        self.id = id
        self.full_duration = duration
        self.full_cooldown = cooldown
        self.duration = duration
        self.cooldown = cooldown

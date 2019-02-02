from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, Namespace, emit, join_room, leave_room
from os import getenv
from pathlib import Path
import logging
from namespaces import HostNamespace, ViewerNamespace, PlayerNamespace
from threading import Timer
from string import ascii_lowercase
from random import choices
from game import Game
from timer import PeriodicTimer

IDENTIFIER_LEN = 6

MIN_PLAYERS_PER_ROOM = 3
MAX_PLAYERS_PER_ROOM = 10

PLAYER_NS_ENDPOINT = '/player'
HOST_NS_ENDPOINT = '/host'
VIEWER_NS_ENDPOINT = '/viewer'

# create logger with '__name__'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

STATIC_FOLDER = getenv("ZOMBEANS_STATIC_FOLDER", default='static')

app = Flask(__name__, static_folder=STATIC_FOLDER)
app.config['STATIC_FOLDER'] = Path(STATIC_FOLDER)
app.config['SECRET_KEY'] = "hey you! don't you dare say anything. Snitches get stitches"
socketio = SocketIO(app, logger=logger)

# Handle first page
@app.route('/')
def main_page():
    return send_from_directory(app.config['STATIC_FOLDER'], 'index.html')

# Handle all static resources
@app.route('/<path:subpath>')
def static_content(subpath):
    return send_from_directory(app.config['STATIC_FOLDER'], subpath)

# Game States
GAME_STATE_LOBBY_WAITING = 1
GAME_STATE_RUNNING = 2
GAME_STATE_FINISHED = 3

# Player States
PLAYER_STATE_NOTHING = 1
PLAYER_STATE_WAITING_GAME_START = 2
PLAYER_STATE_IN_GAME = 3

# Types of clients:
#   - Player: is served controls and joins a room and plays a game
#   - Host: is allowed to control a game starting, is required for a game to exist
#   - Viewer: is served render events

class Server:
    def __init__(self, host_namespace_class, viewer_namespace_class, player_namespace_class):
        self.host_namespace_class = host_namespace_class
        self.viewer_namespace_class = viewer_namespace_class
        self.player_namespace_class = player_namespace_class

        # Map player connection ids to all player data
        self.players = {}
        # Map game connection id to all game data
        self.hosts = {}
        # Map viewer connection id to all viewer data
        self.viewers = {}

    def generate_room_code(self):
        return ''.join(choices(ascii_lowercase, k=IDENTIFIER_LEN)).upper()

    def join_room(self, room, sid, namespace):
        self.socket_io.join_room(room, sid=sid, namespace=namespace)

    def leave_room(self, room, sid, namespace):
        self.socket_io.leave_room(room, sid=sid, namespace=namespace)

    def register(self, socket_io):
        self.socket_io = socket_io

        self.host_namespace = self.host_namespace_class(HOST_NS_ENDPOINT, parent=self)
        self.viewer_namespace = self.viewer_namespace_class(VIEWER_NS_ENDPOINT, parent=self)
        self.player_namespace = self.player_namespace_class(PLAYER_NS_ENDPOINT, parent=self)

        self.socket_io.on_namespace(self.host_namespace)
        self.socket_io.on_namespace(self.viewer_namespace)
        self.socket_io.on_namespace(self.player_namespace)

    def register_host_connect(self, host_id):
        room_code = self.generate_room_code()

        self.hosts[host_id] = {
            'players': [],
            'viewers': [],
            'room_code': room_code,
            'game_state': GAME_STATE_LOBBY_WAITING,
            'game_obj': Game(),
            'game_timer': None
        }

        self.host_namespace.send_room_code(host_id, room_code)

    def register_host_disconnect(self, host_id):
        host = self.hosts[host_id]
        game_state = host['game_state']
        players = host['players']
        viewers = host['viewers']
        room_code = host['room_code']

        if (game_state == GAME_STATE_LOBBY_WAITING) or (game_state == GAME_STATE_RUNNING):
            for player_id in players:
                self.players[player_id]['game_host'] = None
                self.players[player_id]['state'] = PLAYER_STATE_NOTHING

                self.leave_room(room_code, player_id, PLAYER_NS_ENDPOINT)

            for viewer_id in viewers:
                self.viewers[viewer_id]['room_code'] = None

                self.leave_room(room_code, viewer_id, VIEWER_NS_ENDPOINT)

            self.player_namespace.broadcast_game_over(room_code)
            logger.warn(
                "Host disconnected while attending to game (id: {}, room: {})".format(
                    host_id, room_code
                )
            )
        else:
            logger.warn(
                "Host disconnected with invalid state (id: {}, state: {})".format(
                    host_id, game_state
                )
            )

        del self.hosts[host_id]

    def register_viewer_connect(self, viewer_id):
        self.viewers[viewer_id] = {'room_code': None}

    def register_viewer_disconnect(self, viewer_id):
        room_code = self.viewers[viewer_id]['room_code']
        if room_code is not None:
            self.leave_room(room_code, viewer_id, VIEWER_NS_ENDPOINT)

        del self.viewers[viewer_id]

    def register_player_connect(self, player_id):
        self.players[player_id] = {
            'user_name': None,
            'character': None,
            'state': PLAYER_STATE_NOTHING,
            'game_host': None,
        }

    def register_player_disconnect(self, player_id):
        player = self.players[player_id]
        player_state = player['state']
        game_host = player['game_host']

        if (player_state == PLAYER_STATE_WAITING_GAME_START
            ) or (player_state == PLAYER_STATE_IN_GAME):
            self.hosts[game_host]['players'].remove(player_id)
            self.leave_room(self.hosts[game_host]['room_code'], player_id, PLAYER_NS_ENDPOINT)

            logger.warn(
                "Player disconnected while game was running (id: {}, game: {})".format(
                    player_id, game_host
                )
            )
        else:
            logger.warn(
                "Player disconnected with invalid state (id: {}, state: {})".format(
                    player_id, player_state
                )
            )

        del self.players[player_id]

    def register_player_join_request(self, player_id, room_code, user_name):
        player = self.players[player_id]
        host_id = self.lookup_host_by_room_code(room_code)

        if host_id is None:
            logger.info(
                "Player attempted to access non-existent room (id: {}, room: {})".format(
                    player_id, room_code
                )
            )

            self.player_namespace.send_player_join_response(
                player_id, 'failure', 'Room {} does not exist'.format(room_code)
            )
            return

        host = self.hosts[host_id]
        if host['game_state'] != GAME_STATE_LOBBY_WAITING:
            logger.info(
                "Player attempted to join a game that was not in the lobby state (id: {}, room: {})"
                .format(player_id, room_code)
            )

            self.player_namespace.send_player_join_response(
                player_id, 'failure', 'Room {} is not in open state'.format(room_code)
            )
            return

        if len(host['players']) >= MAX_PLAYERS_PER_ROOM:
            logger.info(
                "Player attempted to join a room that was full (id: {}, room: {})".format(
                    player_id, room_code
                )
            )

            self.player_namespace.send_player_join_response(
                player_id, 'failure', 'Room {} is full'.format(room_code)
            )
            return

        host['players'].append(player_id)
        player['state'] = PLAYER_STATE_WAITING_GAME_START
        player['game_host'] = host_id
        player['user_name'] = user_name
        character = len(host['players']) - 1

        self.join_room(room_code, player_id, PLAYER_NS_ENDPOINT)
        self.host_namespace.send_player_joined(host_id, host['players'], user_name)
        self.player_namespace.send_player_join_response(
            player_id, 'success', {
                'room_code': room_code,
                'character': character
            }
        )

    def register_request_start_game(self, host_id):
        host = self.hosts[host_id]
        room_code = host['room_code']
        if len(host['players']) > MIN_PLAYERS_PER_ROOM:
            host['game_state'] = GAME_STATE_RUNNING

            for player_id in host['players']:
                self.players[player_id]['state'] = PLAYER_STATE_IN_GAME

            board_description = host['game_obj'].start()
            self.viewer_namespace.broadcast_game_starting(room_code, board_description)
            self.player_namespace.broadcast_game_starting(room_code)

            def tick_callback(game_obj, room_code):
                tick_data, game_ended = game_obj.tick()
                if game_ended:
                    return True

                self.viewer_namespace.broadcast_game_tick(room_code, tick_data)
                return False

            host['game_timer'] = PeriodicTimer(
                Game.TICK_TIME, tick_callback, args=(host['game_obj'], room_code)
            )
            host['game_timer'].start()

            logger.info("Host started game. (id: {}, room: {})".format(host_id, room_code))
        else:
            logger.warn(
                "Host attempted to start game with insufficient player (id: {}, room: {}, num players: {})"
                .format(host_id, host['room_code'], len(host['players']))
            )

    def lookup_host_by_room_code(self, room_code):
        for host_id, host_data in self.hosts.items():
            if host_data['room_code'] == room_code:
                return host_id
        return None

server = Server(HostNamespace, ViewerNamespace, PlayerNamespace)
server.register(socketio)

if __name__ == '__main__':
    socketio.run(app)

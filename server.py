from string import ascii_lowercase
from random import choices
from namespaces import ViewerNamespace, HostNamespace, PlayerNamespace
import logging

IDENTIFIER_LEN = 6

MIN_PLAYERS_PER_ROOM = 3
MAX_PLAYERS_PER_ROOM = 10

PLAYER_ENDPOINT = '/player'
HOST_ENDPOINT = '/host'
VIEWER_ENDPOINT = '/viewer'

# create logger with '__name__'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

STATIC_FOLDER = getenv("ZOMBEANS_STATIC_FOLDER", default='static')

app = Flask(__name__, static_folder=STATIC_FOLDER)
app.config['STATIC_FOLDER'] = Path(STATIC_FOLDER)
app.config[
    'SECRET_KEY'] = "hey you! don't you dare say anything. Snitches get stitches"
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
GAME_STATE_STARTING = 2
GAME_STATE_RUNNING = 3
GAME_STATE_FINISHED = 4

# Player States
PLAYER_STATE_NOTHING = 1
PLAYER_STATE_WAITING_GAME_START = 2
PLAYER_STATE_IN_GAME = 3

# Types of clients:
#   - Player: is served controls and joins a room and plays a game
#   - Game (host): is served game rendering events
#   - Viewer (optional): is served game rendering events


class Server:
    def __init__(self, host_namespace_class, viewer_namespace_class,
                 player_namespace_class):
        self.host_namespace_class = host_namespace_class
        self.viewer_namespace_class = viewer_namespace_class
        self.player_namespace_class = player_namespace_class

        # Map player connection ids to all player data
        self.players = {}
        # Map game connection id to all game data
        self.hosts = {}
        # Map viewer connection id to all viewer data
        self.viewers = {}
        # Map web connection id to all web data
        self.web_connections = {}

    def generate_room_code(self):
        return ''.join(choices(ascii_lowercase, k=IDENTIFIER_LEN)).upper()

    def join_room(self, room, sid, namespace):
        self.socket_io.join_room(room, sid=sid, namespace=namespace)

    def leave_room(self, room, sid, namespace):
        self.socket_io.leave_room(room, sid=sid, namespace=namespace)

    def register(self, socket_io):
        self.socket_io = socket_io

        self.host_namespace = self.host_namespace_class(
            HOST_ENDPOINT, parent=self)
        self.viewer_namespace = self.viewer_namespace_class(
            VIEWER_ENDPOINT, parent=self)
        self.player_namespace = self.player_namespace_class(
            PLAYER_ENDPOINT, parent=self)

        self.socket_io.on_namespace(self.host_namespace)
        self.socket_io.on_namespace(self.viewer_namespace)
        self.socket_io.on_namespace(self.player_namespace)

    def register_host_connect(self, host_id):
        room_code = self.generate_room_code()

        self.hosts[host_id] = {
            'players': [],
            'room_code': room_code,
            'game_state': GAME_STATE_LOBBY_WAITING
        }

        self.host_namespace.send_room_code(host_id, room_code)

    def register_host_disconnect(self, host_id):
        host = self.hosts[host_id]
        game_state = host['game_state']
        players = host['players']
        room_code = host['room_code']

        if (game_state == GAME_STATE_LOBBY_WAITING) or (
                game_state == GAME_STATE_STARTING) or (
                    game_state == GAME_STATE_RUNNING):
            for player_id in players:
                self.players[player_id]['game_host'] = None
                self.players[player_id]['state'] = PLAYER_STATE_NOTHING

            self.player_namespace.broadcast_game_over(room_code)
            logger.warn(
                "Host disconnected while attending to game (id: {}, room: {})".
                format(host_id, room_code))
        else:
            logger.warn(
                "Host disconnected with invalid state (id: {}, state: {})".
                format(host_id, game_state))

        del self.hosts[host_id]

    def register_viewer_connect(self, viewer_id):
        self.viewers[viewer_id] = {'room_code': None}

    def register_viewer_disconnect(self, viewer_id):
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

        if (player_state == PLAYER_STATE_WAITING_GAME_START) or (
                player_state == PLAYER_STATE_IN_GAME):
            self.hosts[game_host]['players'].remove(player_id)
            logger.warn(
                "Player disconnected while game was running (id: {}, game: {})"
                .format(player_id, game_host))
        else:
            logger.warn(
                "Player disconnected with invalid state (id: {}, state: {})".
                format(player_id, player_state))

        del self.players[player_id]

    def register_player_join_request(self, player_id, room_number, user_name):
        pass


server = Server(HostNamespace, ViewerNamespace, PlayerNamespace)
server.register(socketio)

if __name__ == '__main__':
    socketio.run(app)

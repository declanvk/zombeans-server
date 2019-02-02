from string import ascii_lowercase
from random import choices
from namespaces import ViewerNamespace, HostNamespace, PlayerNamespace

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

# Types of clients:
#   - Player: is served controls and joins a room and plays a game
#   - Game (host): is served game rendering events
#   - Viewer (optional): is served game rendering events

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
        # Map web connection id to all web data
        self.web_connections = {}

    def generate_lounge_id(self):
        return ''.join(choices(ascii_lowercase, k=IDENTIFIER_LEN)).upper()

    def register(self, socket_io)
        self.socket_io = socket_io

        self.host_namespace = self.host_namespace_class(HOST_ENDPOINT, parent=self)
        self.viewer_namespace = self.viewer_namespace_class(VIEWER_ENDPOINT, parent=self)
        self.player_namespace = self.player_namespace_class(PLAYER_ENDPOINT, parent=self)

        self.socket_io.on_namespace(self.host_namespace)
        self.socket_io.on_namespace(self.viewer_namespace)
        self.socket_io.on_namespace(self.player_namespace)

    def register_host_connect(self, player_id):
        pass

    def register_host_disconnect(self, player_id):
        pass

    def register_viewer_connect(self, player_id):
        pass

    def register_viewer_disconnect(self, player_id):
        pass

    def register_player_connect(self, player_id):
        pass

    def register_player_disconnect(self, player_id):
        pass


server = Server(HostNamespace, ViewerNamespace, PlayerNamespace)
server.register(socketio)

if __name__ == '__main__':
    socketio.run(app)

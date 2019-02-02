from flask import request
from flask_socketio import Namespace, emit
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Namesapces:
#   - Manage types of clients/connections
#   - functions are of two types:
#       - on_"event type": this type of function is used to receive message/events
#       - send_"event type": this type of function is used to send messages/events to a single entity
#       - broadcast_"event type": this type of function is used to send messages/events to a group of entities

class HostNamespace(Namespace):
    def __init__(self, *args, **kwargs):
        super(HostNamespace,
              self).__init__(*args, **{key: kwargs[key]
                                       for key in kwargs
                                       if key != 'parent'})

        if 'parent' not in kwargs:
            raise ValueError("'parent' keyword not found in namespace init")

        self.parent = kwargs['parent']

    def on_connect(self):
        self.parent.register_host_connect(request.sid)

    def on_disconnect(self):
        self.parent.register_host_disconnect(request.sid)

    def send_room_code(self, host_id, room_code):
        self.emit('room_code', {'pkt_name': 'room_code', 'room_code': room_code}, room=host_id)

    def send_player_joined(self, host_id, players, new_player_name):
        self.emit(
            'player_joined', {
                'pkt_name': 'player_joined',
                'players': list(players),
                'new_player_name': new_player_name
            },
            room=host_id
        )

    def on_request_start_game(self, data):
        host_id = request.sid
        self.parent.register_request_start_game(host_id)

class ViewerNamespace(Namespace):
    def __init__(self, *args, **kwargs):
        super(ViewerNamespace,
              self).__init__(*args, **{key: kwargs[key]
                                       for key in kwargs
                                       if key != 'parent'})

        if 'parent' not in kwargs:
            raise ValueError("'parent' keyword not found in namespace init")

        self.parent = kwargs['parent']

    def on_connect(self):
        self.parent.register_viewer_connect(request.sid)

    def on_disconnect(self):
        self.parent.register_viewer_disconnect(request.sid)

    def broadcast_game_starting(self, room_id, board_description):
        self.emit(
            'game_starting', {
                'pkt_name': 'game_starting',
                'board_description': board_description
            },
            room=room_id
        )

    def broadcast_game_tick(self, room_id, player_pos_data):
        self.emit(
            'game_tick', {
                'pkt_name': 'game_tick',
                'player_pos_data': player_pos_data
            },
            room=room_id
        )

    def send_game_view_response(self, viewer_id, view_status, view_status_data):
        self.emit(
            'game_view_response', {
                'pkt_name': 'game_view_response',
                'view_status': view_status,
                'view_status_data': view_status_data
            },
            room=viewer_id
        )

    def on_request_game_view(self, payload):
        viewer_id = request.sid
        room_code = payload['room_code']

        self.parent.register_request_game_view(viewer_id, room_code)

class PlayerNamespace(Namespace):
    def __init__(self, *args, **kwargs):
        super(PlayerNamespace,
              self).__init__(*args, **{key: kwargs[key]
                                       for key in kwargs
                                       if key != 'parent'})

        if 'parent' not in kwargs:
            raise ValueError("'parent' keyword not found in namespace init")

        self.parent = kwargs['parent']

    def on_connect(self):
        self.parent.register_player_connect(request.sid)

    def on_disconnect(self):
        self.parent.register_player_disconnect(request.sid)

    def send_player_join_response(self, player_id, status, aux_data):
        self.emit(
            'player_join_response', {
                'pkt_name': 'player_join_response',
                'status': status,
                'aux_data': aux_data
            },
            room=player_id
        )

    def broadcast_game_starting(self, room_id):
        self.emit('game_starting', {'pkt_name': 'game_starting'}, room=room_id)

    def broadcast_game_over(self, room_id):
        self.emit('game_over', {'pkt_name': 'game_over'}, room=room_id)

    def on_player_join_request(self, payload):
        room_code = payload['room_code']
        user_name = payload['user_name']
        player_id = request.sid

        self.parent.register_player_join_request(player_id, room_code, user_name)

    def on_make_move(self, payload):
        player_id = request.sid
        origin = payload['origin']
        action = payload['action']

        self.parent.register_make_move(player_id, origin, action)

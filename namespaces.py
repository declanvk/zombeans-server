from flask import request
from flask_socketio import Namespace, emit, join_room, leave_room

from json import loads

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Namesapces:
#   - Manage types of clients/connections
#   - functions are of two types:
#       - on_"event type": this type of function is
#         used to receive message/events
#       - send_"event type": this type of function
#         is used to send messages/events to a single entity
#       - broadcast_"event type": this type of function
#         is used to send messages/events to a group of entities

class HostNamespace(Namespace):

    def __init__(self, *args, **kwargs):
        super(HostNamespace, self).__init__(*args, **{key: kwargs[key] for key in kwargs if key != 'parent'})

        if 'parent' not in kwargs:
            raise ValueError("'parent' keyword not found in namespace init")

        self.parent = kwargs['parent']

    def on_connect(self):
        self.parent.register_host_connect(request.sid)

    def on_disconnect(self):
        self.parent.register_host_disconnect(request.sid)

    def send_room_code(self, host_id, room_code):
        self.emit('room_code', { 'pkt_name': 'room_code', 'room_code': room_code }, room=host_id)

    def send_player_joined(self, host_id, players, new_player_name):
        self.emit('player_joined', {
            'pkt_name': 'player_joined',
            'players': players,
            'new_player_name': new_player_name
        }, room=host_id)

class ViewerNamespace(Namespace):

    def __init__(self, *args, **kwargs):
        super(ViewerNamespace, self).__init__(*args, **{key: kwargs[key] for key in kwargs if key != 'parent'})

        if 'parent' not in kwargs:
            raise ValueError("'parent' keyword not found in namespace init")

        self.parent = kwargs['parent']

    def on_connect(self):
        self.parent.register_viewer_connect(request.sid)

    def on_disconnect(self):
        self.parent.register_viewer_disconnect(request.sid)

    def broadcast_game_starting(self, room_id):
        self.emit('game_starting', { 'pkt_name': 'game_starting' }, room=room_id)

    def broadcast_game_tick(self, room_id, player_pos_data):
        self.emit('game_tick', {
            'pkt_name': 'game_tick',
            'player_pos_data': player_pos_data
        }, room=room_id)

    def send_game_view_response(self, viewer_id, view_status, view_status_data):
        self.emit('game_view_response', {
            'pkt_name': 'game_view_response',
            'view_status': view_status,
            'view_status_data': view_status_data
        }, room=viewer_id)

class PlayerNamespace(Namespace):

    def __init__(self, *args, **kwargs):
        super(PlayerNamespace, self).__init__(*args, **{key: kwargs[key] for key in kwargs if key != 'parent'})

        if 'parent' not in kwargs:
            raise ValueError("'parent' keyword not found in namespace init")

        self.parent = kwargs['parent']

    def on_connect(self):
        self.parent.register_player_connect(request.sid)

    def on_disconnect(self):
        self.parent.register_player_disconnect(request.sid)

    def send_player_join_response(self, player_id, room_number, user_name, join_status, failure_reason=None):
        self.emit('player_join_response', {
            'pkt_name': 'player_join_response',
            'room_number': room_number,
            'user_name': user_name,
            'join_status': {
                'status': join_status,
                'failure_reason': failure_reason if failure_reason is not None else ""
            }
        }, room=player_id)

    def broadcast_game_starting(self, room_id):
        self.emit('game_starting', { 'pkt_name': 'game_starting' }, room=room_id)

    def broadcast_game_over(self, room_id):
        self.emit('game_over', { 'pkt_name': 'game_over' }, room=room_id)


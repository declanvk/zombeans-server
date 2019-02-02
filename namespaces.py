from flask import request
from flask_socketio import Namespace, emit, join_room, leave_room

from json import loads

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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

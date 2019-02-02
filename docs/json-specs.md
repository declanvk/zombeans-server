
## Room Code (1)
Sent from server to web client as soon as socket is opened

```json
{
    "pkt_name": "room_code",
    "room_code": "room code (string)"
}
```

## Player Join Request (2)
Sent from mobile client to server when user types in code/name.

```json
{
    "pkt_name": "player_join_request",
    "room_number": "room number (string)",
    "user_name": "user name (string)",
}
```

## Player Join Response (3)
Sent from server to mobile to notify successful room join.

```json
{
    "pkt_name": "player_join_response",
    "room_number": "room number (string)",
    "user_name": "user name (string)",
    "join_status": {
       "status": "success" | "failure",
       "failure_reason": "failure reason (string)"
    }
}
```


## Player Joined (4)
Sent from server to web client when a player joins. Packet include ALL currently joined players.

```json
{
    "pkt_name": "player_joined",
    "players": [
        {"user_name": "user 1 name (string)", "character": "character name (string)"},
        {"user_name": "user 2 name (string)", "character": "character name (string)"}
    ],
    "new_player_name": "new player name (string)"
}
```

## Request Game Start (5)
Sent from web client to server to start game

```json
{
    "pkt_name": "request_start_game"
}
```

## Game Starting (6)
Sent from server to mobile client and web client when the game starts

```json
{
    "pkt_name": "game_starting",
}
```

## Make Move (7)
Sent from mobile client to server when a button state changes

```json
{
    "pkt_name": "make_move",
    "move_data": "???"
}
```

## Game Tick (8)
Sent from server to all viewers

```json
{
    "pkt_name": "game_tick",
    "player_pos_data": ["???"]
}
```

## Become Zombie (9)
Sent from server to player to inform them they've become a zombie

```json
{
    "pkt_name": "become_zombie"
}
```

## Game Over (10)
Sent from server to players to notify game end

```json
{
    "pkt_name": "become_zombie",
    "game_end_data": "???"
}
```
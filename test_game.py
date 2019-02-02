import game
from game import Direction, KeyAction

game = game.Game()
game.add_player(1)
game.add_player(2)
game.add_player(3)
game.add_player(4)
game.add_player(5)
game.add_player(6)
game.add_player(7)
game.start()
game.input(1, Direction.UP, KeyAction.PRESSED)
for _ in range(50):
    print(game.tick())
game.input(1, Direction.UP, KeyAction.RELEASED)
game.input(1, Direction.DOWN, KeyAction.PRESSED)
game.input(1, Direction.RIGHT, KeyAction.PRESSED)
for i in range(25):
    print(game.tick())
y_pos = 0
while y_pos > -2490:
    x = game.tick()
    y_pos = x[0][1]['position'][1]
    print(y_pos)
    print(x)

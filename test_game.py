import game

game = game.Game()
game.add_player(1)
game.add_player(2)
game.add_player(3)
game.add_player(4)
game.add_player(5)
game.add_player(6)
game.add_player(7)
game.start()
game.input(1, "w_pressed")
for _ in range(50):
    print(game.tick())
game.input(1, "w_released")
game.input(1, "s_pressed")
game.input(1, "d_pressed")
for i in range(25):
    print(game.tick())
y_pos = 0
while y_pos > -2490:
    x = game.tick()
    y_pos = x[0][1]['position'][1]
    print(y_pos)
    print(x)


import game

game = game.Game()
game.add_player(1)
game.add_player(2)
game.start()
for i in range(10):
    print(game.tick())
    game.input(1, "w_pressed")
game.input(1, "w_released")
game.input(1, "s_pressed")
game.input(1, "d_pressed")
for i in range(25):
    print(game.tick())


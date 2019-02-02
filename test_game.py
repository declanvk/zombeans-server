import game

game = game.Game()
game.add_player(1)
game.add_player(2)
game.start()
while(True):
    print(game.tick())

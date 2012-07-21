import textwrap
import math
import libtcodpy as libtcod
libtcod.console_set_keyboard_repeat(500, 50)
libtcod.namegen_parse('../data/namegen/jice_norse.cfg')
libtcod.namegen_parse('../data/namegen/jice_fantasy.cfg')
libtcod.namegen_parse('../data/namegen/jice_celtic.cfg')

from game import *
if __name__ == 'test1':
	game_instance = Game()

if __name__ == '__main__':
	from test1 import game_instance
	from items import *
	from utilities import *
	from maps import *
	from objects import *
	from monsters import *


	from functools import partial
	render_bar = partial(render_bar, game_instance.panel)

	game_instance.setup_map()
	game_instance.main()


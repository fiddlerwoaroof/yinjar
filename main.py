import os.path
import textwrap
import math
import libtcodpy as libtcod
import glob
libtcod.console_set_keyboard_repeat(500, 50)
for file in glob.glob('./data/namegen/*.cfg'):
	libtcod.namegen_parse(file)

help = '''
 'i': Inventory
 'd': Drop
 'g': Get item (Pick up)
 '?': Help
 Alt+Escape: Exit

 Arrow Keys for movement / selecting
 Name of item under the mouse shown
 above the health bar
'''

from game import GameBase
import levels
import objects
import utilities
if __name__ == 'main':
	class Game(GameBase):
		#actual size of the window
		SCREEN_WIDTH, SCREEN_HEIGHT = 155, 90

		MAP_WIDTH, MAP_HEIGHT = SCREEN_WIDTH, SCREEN_HEIGHT - 17

		INVENTORY_WIDTH = 50
		BAR_WIDTH = 25

		PANEL_HEIGHT = SCREEN_HEIGHT - MAP_HEIGHT - 2
		PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

		MSG_X = BAR_WIDTH + 2
		MSG_WIDTH, MSG_HEIGHT = SCREEN_WIDTH - BAR_WIDTH - 2, PANEL_HEIGHT - 1

		ROOM_MIN_SIZE, ROOM_MAX_SIZE = 7, 19

		MAX_ROOMS = 51

		MAX_ROOM_MONSTERS, MAX_ROOM_ITEMS = 9, 6

		CONFUSE_NUM_TURNS = 17

		LIMIT_FPS = 20	#20 frames-per-second maximum

		def __init__(self):
			GameBase.__init__(self, 'caer flinding', self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

			self.select_cb = None

			self.panel = libtcod.console_new(self.SCREEN_WIDTH, self.PANEL_HEIGHT)

			self.levels = []

			self.current_level = 0
			self.levels = [levels.Level(self.MAP_WIDTH, self.MAP_HEIGHT, self.con, self.item_types, self.monster_types)]

			x,y = None,None
			self.player = objects.Player(self.level.map, self.con, x,y, '@', libtcod.white,
				fighter=objects.Fighter(hp=20, defense = 2, power = 10, death_function=self.player_death)
			)



		def player_death(self, player):
			self.message('You died!', libtcod.red)
			self.game_state = 'dead'
			player.char = '%'
			player.color = libtcod.dark_red

		def setup_map(self):
			print self.monster_types
			self.player.enter_level(self.level)

			self.level.setup(self.MAX_ROOMS,
				self.ROOM_MIN_SIZE, self.ROOM_MAX_SIZE,
				self.MAX_ROOM_MONSTERS, self.MAX_ROOM_ITEMS
			)
			self.set_fov()

		def set_fov(self):
			self.player.enter_level(self.level)
			self.level.init_fov()
			self.level.recompute_fov(True)

		item_types = {}
		@classmethod
		def register_item_type(cls, chance):
			def _inner(typ):
				cls.item_types[typ] = chance
				return typ
			return _inner


		monster_types = {}
		@classmethod
		def register_monster_type(cls, typ, chance):
			cls.monster_types[typ] = chance
			return typ

		@property
		def level(self):
			return self.levels[self.current_level]

		@property
		def map(self):
			return self.level.map

		def change_level(self, down=True):
			change = 1 if down else -1
			self.current_level += change

			if (
					(self.current_level < 0 and not down)
						or
					(self.current_level >= len(self.levels))
			):
				print 'hello'
				new_level = levels.Level(
					self.MAP_WIDTH, self.MAP_HEIGHT,
					self.con, self.item_types, self.monster_types
				)

				if down:
					self.levels.append(new_level)
				else:
					self.levels.insert(0,new_level)
				self.current_level = self.levels.index(new_level)
				self.setup_map()
			else:
				self.set_fov()



		def main(self):
			self.message('Welcome %s! Prepare to perish in the Tombs of the Ancient Kings.' % self.player.name,
				libtcod.red
			)
			for x in GameBase.main(self):
				if x == 1:
					if (
						self.game_state in ('playing','selecting')
							and
						self.player_action != 'didnt-take-turn'
					):
						for object in self.level.objects:
							if object.ai:
								object.clear()
								object.ai.take_turn()


					for object in self.level.objects:
						object.clear()

					if self.game_state == 'selecting':
						self.cursor.clear()

				elif x == 2:
					if self.player_action == 'move':
						self.player.tick()




		def do_playing(self):
			if self.player_action != 'didnt-take-turn':
				for object in self.level.iter_objects():
					if object.ai:
						object.clear()
						object.ai.take_turn()
			self.player.clear()

			if self.player_action == 'move':
				self.player.tick()

		def do_selecting(self):
			self.cursor.clear()

		def do_dead(self):
			pass


		mvkeyhandler = utilities.MovementKeyListener()
		@mvkeyhandler.up
		def mvkeyhandler(self):
			self.player.move_or_attack(0,-1)
			return 'move'

		@mvkeyhandler.down
		def mvkeyhandler(self):
			self.player.move_or_attack(0, 1)
			return 'move'

		@mvkeyhandler.left
		def mvkeyhandler(self):
			self.player.move_or_attack(-1, 0)
			return 'move'

		@mvkeyhandler.right
		def mvkeyhandler(self):
			self.player.move_or_attack(1, 0)
			return 'move'

		@mvkeyhandler.handle('i')
		def mvkeyhandler(self):
			item = self.inventory_menu('choose item\n')
			if item is not None:
				item.bind_game(self)
				self.player.use(item)

		@mvkeyhandler.handle('d')
		def mvkeyhandler(self):
			chosen_item = self.inventory_menu('Choose the item to drop:')
			if chosen_item is not None:
				self.player.drop(chosen_item.owner)

		@mvkeyhandler.handle('g')
		def mvkeyhandler(self):
			for obj in self.level.iter_objects():
						if obj.x == self.player.x and obj.y == self.player.y and obj.item:
							self.player.pick_up(obj)

		@mvkeyhandler.handle('<')
		def mvkeyhandler(self):
			self.change_level(down=False)

		@mvkeyhandler.handle('>')
		def mvkeyhandler(self):
			self.change_level(down=True)

		@mvkeyhandler.handle('?')
		def mvkeyhandler(self):
			self.menu(help, [], 50)

		selectkeyhandler = utilities.MovementKeyListener()
		@selectkeyhandler.up
		def selectkeyhandler(self):
			self.cursor.y -= 1
		@selectkeyhandler.down
		def selectkeyhandler(self):
			self.cursor.y += 1
		@selectkeyhandler.left
		def selectkeyhandler(self):
			self.cursor.x -= 1
		@selectkeyhandler.right
		def selectkeyhandler(self):
			self.cursor.x += 1

		@selectkeyhandler.handle(libtcod.KEY_ENTER)
		def selectkeyhandler(self):
			self.select_cb(self.cursor.x, self.cursor.y)
			self.cursor.clear()
			self.game_state = 'playing'



		def render_all(self):
			for obj in self.level.iter_objects():
				if obj != self.player:
					obj.draw(self.player)
			self.player.draw()

			if self.game_state == 'selecting':
				self.cursor.draw()

			if self.player.fov_recompute:
				self.level.recompute_fov()

			libtcod.console_blit(self.con, 0,0, self.SCREEN_WIDTH,self.SCREEN_HEIGHT, 0,0, 0)

			libtcod.console_set_default_background(self.panel, libtcod.black)
			libtcod.console_clear(self.panel)

			utilities.render_bar(self.panel, 1,1, self.BAR_WIDTH, 'HP',
				self.player.fighter.hp,
				self.player.fighter.max_hp,
				libtcod.red,
				libtcod.darker_red
			)

			libtcod.console_print_ex(self.panel, self.BAR_WIDTH/2,3, libtcod.BKGND_NONE, libtcod.CENTER,
				'%s p %s d' %(self.player.fighter.power, self.player.fighter.defense)
			)

			libtcod.console_set_default_foreground(self.panel, libtcod.light_gray)
			libtcod.console_print(self.panel, 1, 0, self.get_names_under_mouse())

			y = 1
			for line, color in self.game_msgs:
				libtcod.console_set_default_foreground(self.panel, color)
				libtcod.console_print_ex(self.panel, self.MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
				y += 1


			libtcod.console_blit(self.panel, 0,0, self.SCREEN_WIDTH,self.PANEL_HEIGHT, 0,0, self.PANEL_Y)

		def main_menu(self):
			message = (
				'Welcome to YinJAR: is not Just Another Roguelike (WIP)',
				'',
				'Choose an option:',
				'',
			)

			options = ['Play', 'Exit']
			return options[
				self.menu('\n'.join(message), options, len(message[0]))
			]

	game_instance = Game()
	from monsters import MonsterLoader


if __name__ == '__main__':
	from main import game_instance
	from items import *
	from utilities import *
	from maps import *
	from objects import *
	from monsters import *


	from functools import partial
	render_bar = partial(render_bar, game_instance.panel)

	ml = MonsterLoader(os.path.join('.','data','monsters'))
	ml.load_monsters()

	il = ItemLoader(os.path.join('.','data','items'))
	il.load_items()

	action = game_instance.main_menu()
	if action.lower() == 'play':
		game_instance.setup_map()
		game_instance.main()


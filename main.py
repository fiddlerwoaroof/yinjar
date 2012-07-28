import os.path
import yaml
import textwrap
import math
import libtcodpy as libtcod
import glob
libtcod.console_set_keyboard_repeat(500, 50)
for fil in glob.glob('./data/namegen/*.cfg'):
	libtcod.namegen_parse(fil)

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
	class Null: pass
	class SettingsObject(object):
		def __init__(self, setting_name, default=Null):
			self.setting_name = setting_name
			self.default = default

		def __get__(self, instance, owner):
			result = instance.settings.get(self.setting_name, self.default)
			if result is Null:
				raise KeyError('%s is not specified in the configuration' % self.setting_name)
			return result

	class Game(GameBase):
		#actual size of the window
		def load_settings(self):
			self.settings = yaml.safe_load(
				file(os.path.join('./data/main.yml'))
			)
			if self.settings == None:
				self.settings = {}
			print self.settings

		SCREEN_WIDTH = SettingsObject('screen_width', 80)
		SCREEN_HEIGHT = SettingsObject('screen_height', 50)

		PANEL_HEIGHT = 15

		INVENTORY_WIDTH = 50

		@property
		def MAP_WIDTH(self):
			return self.SCREEN_WIDTH
		@property
		def MAP_HEIGHT(self):
			return self.SCREEN_HEIGHT - (self.PANEL_HEIGHT + 2)


		BAR_WIDTH = 25
		MSG_X = BAR_WIDTH + 2
		MSG_HEIGHT = PANEL_HEIGHT

		@property
		def PANEL_Y(self):
			return self.SCREEN_HEIGHT - self.PANEL_HEIGHT

		@property
		def MSG_WIDTH(self):
			return self.SCREEN_WIDTH - self.MSG_X

		@property
		def MSG_HEIGHT(self):
			return self.PANEL_HEIGHT - 1

		ROOM_MIN_SIZE = SettingsObject('room_min_wall_length', 4)
		ROOM_MAX_SIZE = SettingsObject('room_max_wall_length', 7)

		MAX_ROOMS = SettingsObject('max_number_rooms', 10)
		MAX_ROOM_MONSTERS = SettingsObject('max_number_room_monsters', 6)
		MAX_ROOM_ITEMS = SettingsObject('max_number_room_items', 3)

		CONFUSE_NUM_TURNS = 17

		LIMIT_FPS = 20	#20 frames-per-second maximum

		def __init__(self):
			self.load_settings()
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
			item = self.inventory_menu('Choose item to use\n')
			if item is not None:
				item.bind_game(self)
				self.player.use(item)

		@mvkeyhandler.handle('d')
		def mvkeyhandler(self):
			chosen_item = self.inventory_menu('Choose item to drop\n')
			if chosen_item is not None:
				self.player.drop(chosen_item.owner)

		@mvkeyhandler.handle('n')
		def mvkeyhandler(self):
			chosen_item = self.inventory_menu('Choose item to unmod\n')
			if chosen_item is not None:
				data = chosen_item.mods.keys()
				index = self.menu('Choose \nmod to \nundo\n', data, self.INVENTORY_WIDTH)
				if index is not None:
					self.player.unmodify(chosen_item.name, data[index])

		@mvkeyhandler.handle('m')
		def mvkeyhandler(self):
			chosen_item = self.inventory_menu('Choose item to mod\n')
			if chosen_item is not None:
				chosen_mod = self.mod_menu('Choose mod to apply\n')
				if chosen_mod is not None:
					self.player.modify(chosen_item.name, chosen_mod.name)

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

	game_instance.load_settings()
	action = game_instance.main_menu()
	if action.lower() == 'play':
		game_instance.setup_map()
		game_instance.main()


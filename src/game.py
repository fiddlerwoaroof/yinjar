import libtcodpy as libtcod
import maps
import objects
import utilities
import levels

class Cursor(object):
	def __init__(self, con, char, x,y):
		self.con = con
		self.char = char
		self.color = libtcod.white
		self.x = x
		self.y = y

	def draw(self):
		libtcod.console_set_default_foreground(self.con, self.color)
		libtcod.console_put_char(self.con, self.x,self.y, self.char, libtcod.BKGND_NONE)

	def clear(self):
		libtcod.console_put_char(self.con, self.x,self.y, ' ', libtcod.BKGND_NONE)



class Game:
	#actual size of the window
	SCREEN_WIDTH, SCREEN_HEIGHT = 155, 90

	libtcod.console_init_root(
		SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False
	)

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

	color_dark_wall = libtcod.Color(60, 60, 60)
	color_light_wall = libtcod.Color(127,127,127)
	color_dark_ground = libtcod.Color(150,150,150)
	color_light_ground = libtcod.Color(200,200,200)

	con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
	cursor = Cursor(con, 'X', 0,0)
	select_cb = None

	game_msgs = []

	game_state = 'playing'


	panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

	key = libtcod.Key()
	mouse = libtcod.Mouse()

	def __init__(self):
		print '__init__'
		self.player_action = 'didnt-take-turn'
		x,y = self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2

		self.player = objects.Player(self.map, self.con, x,y, '@', libtcod.white,
			fighter=objects.Fighter(hp=20, defense = 2, power = 10, death_function=self.player_death)
		).enter_level(self.level)

		libtcod.sys_set_fps(self.LIMIT_FPS)

	def select(self, cb):
		self.game_state = 'selecting'
		self.select_cb = cb
		self.cursor.x, self.cursor.y = self.player.x, self.player.y

	def player_death(self, player):
		utilities.message(self.game_msgs, self.MSG_HEIGHT, self.MSG_WIDTH, 'You died!')
		self.game_state = 'dead'
		player.char = '%'
		player.color = libtcod.dark_red

	def setup_map(self):
		self.level.setup(self.MAX_ROOMS,
			self.ROOM_MIN_SIZE, self.ROOM_MAX_SIZE,
			self.MAX_ROOM_MONSTERS, self.MAX_ROOM_ITEMS
		)
		self.player.init_fov()


	item_types = {}
	@classmethod
	def register_item_type(cls, chance):
		def _inner(typ):
			cls.item_types[typ] = chance
			return cls
		return _inner


	monster_types = {}
	@classmethod
	def register_monster_type(cls, typ, chance):
		cls.monster_types[typ] = chance

	levels = [levels.Level(MAP_WIDTH, MAP_HEIGHT, con, item_types, monster_types)]
	current_level = 0
	@property
	def level(self):
		return self.levels[self.current_level]

	@property
	def map(self):
		return self.level.map

	def change_level(self, down=True):
		change = 1 if down else -1

		if self.current_level == 0 or change >= len(self.levels):
			new_level = levels.Level(
				self.MAP_WIDTH, self.MAP_HEIGHT,
				self.con, self.item_types, self.monster_types
			)

			if down:
				self.levels.append(new_level)
			else:
				self.levels.insert(0,new_level)

		self.current_level += change

		if (self.current_level == 0 and down == False) or change >= len(self.levels):
			self.setup_map()
		else:
			self.recalculate_fov_params()

		self.player.enter_level(self.level)

	def main(self):
		libtcod.console_set_default_foreground(0, libtcod.white)
		libtcod.console_set_default_foreground(self.con, libtcod.white)

		message('Welcome %s! Prepare to perish in the Tombs of the Ancient Kings.' % self.player.name,
			libtcod.red
		)


		while not libtcod.console_is_window_closed():
			self.render_all()
			libtcod.console_flush()

			if self.game_state in ('playing','selecting') and self.player_action != 'didnt-take-turn':
				for object in self.level.objects:
					if object.ai:
						object.clear()
						object.ai.take_turn()


			for object in self.level.objects:
				object.clear()

			if self.game_state == 'selecting':
				self.cursor.clear()

			self.handle_keys()

			if self.player_action == 'exit':
				break

			elif self.player_action == 'move':
				self.player.tick()


	def handle_keys(self):
		libtcod.sys_check_for_event(
			libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE|libtcod.KEY_PRESSED,
			self.key,self.mouse
		)

		self.player_action = 'didnt-take-turn'
		if self.game_state == 'playing':
			if self.key.vk == libtcod.KEY_UP:
				self.player.move_or_attack(0, -1)
				self.player_action = 'move'
			elif self.key.vk == libtcod.KEY_DOWN:
				self.player.move_or_attack(0, 1)
				self.player_action = 'move'
			elif self.key.vk == libtcod.KEY_LEFT:
				self.player.move_or_attack(-1, 0)
				self.player_action = 'move'
			elif self.key.vk == libtcod.KEY_RIGHT:
				self.player.move_or_attack(1, 0)
				self.player_action = 'move'
			else:
				key_char = chr(self.key.c)

				if key_char == 'i':
					item = self.inventory_menu('choose item\n')
					print item
					if item is not None:
						self.player.use(item)

				elif key_char == 'd':
					chosen_item = inventory_menu('Choose the item to drop:')
					if chosen_item is not None:
						self.player.drop(chosen_item)

				elif key_char == 'g':
					print [x.item for x in self.level.objects]
					for obj in self.level.objects:
						if obj.x == self.player.x and obj.y == self.player.y and obj.item:
							self.player.pick_up(obj)

				elif key_char == '<':
					self.change_level(down=False)
				elif key_char == '>':
					self.change_level(down=True)

		elif self.game_state == 'selecting':
			if self.key.vk == libtcod.KEY_UP:
				self.cursor.y -= 1
			elif self.key.vk == libtcod.KEY_DOWN:
				self.cursor.y += 1
			elif self.key.vk == libtcod.KEY_LEFT:
				self.cursor.x -= 1
			elif self.key.vk == libtcod.KEY_RIGHT:
				self.cursor.x += 1
			elif self.key.vk == libtcod.KEY_ENTER:
				self.select_cb(self.cursor.x, self.cursor.y)
				self.cursor.clear()
				self.game_state = 'playing'

		if self.key.vk == libtcod.KEY_ESCAPE and self.key.lalt:
			self.player_action = 'exit'

		return self.player_action

	def render_all(self):
		for obj in self.level.objects:
			if obj != self.player:
				obj.draw(self.player)

		self.player.draw()

		if self.game_state == 'selecting':
			self.cursor.draw()

		if self.player.fov_recompute:
			self.player.recompute_fov()

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

	def inventory_menu(self, header):
		index = menu(header, self.player.get_item_names(), Game.INVENTORY_WIDTH)

		if index is not None:
			return self.player.get_item(index)

	def get_names_under_mouse(self):
		x,y = self.mouse.cx, self.mouse.cy
		names = ', '.join(
			obj.name for obj in self.level.objects
				if
			(obj.x,obj.y) == (x,y)
				and
			self.player.can_see(obj)
		)
		return names.capitalize()

from functools import partial
message = partial(utilities.message, Game.game_msgs, Game.MSG_HEIGHT, Game.MSG_WIDTH)

import items


def menu(header, options, width):
	if len(options) > 26: raise ValueError('too many items')

	header_height = libtcod.console_get_height_rect(Game.con, 0,0, width,Game.SCREEN_HEIGHT, header)
	height = len(options) + header_height

	window = libtcod.console_new(width, height)

	libtcod.console_set_default_foreground(window, libtcod.white)
	libtcod.console_print_rect(window, 0,0, width,height, header)

	y = header_height
	for option_text in zip('abcdefghijklmnopqrstuvwxyz', options):
		text = '(%s) %s' % option_text
		libtcod.console_print(window, 0, y, text)
		y += 1

	x = Game.SCREEN_WIDTH/2 - width/2
	y = Game.SCREEN_HEIGHT/2 - height/2
	libtcod.console_blit(window, 0,0, width,height, 0, x,y, 1.0, 0.7)

	libtcod.console_flush()
	libtcod.sys_wait_for_event(libtcod.KEY_PRESSED, Game.key, Game.mouse, True)

	index = Game.key.c - ord('a')
	if index >= 0 and index < len(options): return index
	return None



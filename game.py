import libtcodpy as libtcod
import maps
import objects
import utilities
import levels
import functools

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

class GameBase:
	#actual size of the window
	SCREEN_WIDTH, SCREEN_HEIGHT = 50,70

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


	def message(self, msg, color=None):
		if color is not None:
			utilities.message(self.game_msgs, self.MSG_HEIGHT, self.MSG_WIDTH, msg, color)
		else:
			utilities.message(self.game_msgs, self.MSG_HEIGHT, self.MSG_WIDTH, msg)

	def __init__(self, app_name='test app', screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT):
		print '__init__'
		libtcod.console_init_root(
			screen_width, screen_height, app_name, False
		)

		self.game_msgs = []
		global message
		message = functools.partial(utilities.message, self.game_msgs, self.MSG_HEIGHT, self.MSG_WIDTH)

		self.game_state = 'playing'
		self.player_action = 'didnt-take-turn'

		x,y = None,None

		self.con = libtcod.console_new(self.MAP_WIDTH, self.MAP_HEIGHT)
		self.panel = libtcod.console_new(self.SCREEN_WIDTH, self.PANEL_HEIGHT)
		self.cursor = Cursor(self.con, 'X', 0,0)

		self.key = libtcod.Key()
		self.mouse = libtcod.Mouse()

		libtcod.sys_set_fps(self.LIMIT_FPS)


	def main(self):
		libtcod.console_set_default_foreground(0, libtcod.white)
		libtcod.console_set_default_foreground(self.con, libtcod.white)

		message('Welcome to the arena!')

		while not libtcod.console_is_window_closed():
			yield 0

			self.render_all()
			libtcod.console_flush()

			yield 1

			self.handle_keys()

			yield 2

			if self.player_action == 'exit':
				break

	def select(self, cb):
		self.game_state = 'selecting'
		self.select_cb = cb
		self.cursor.x, self.cursor.y = self.player.x, self.player.y


	def handle_keys(self):
		libtcod.sys_check_for_event(
			libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE|libtcod.KEY_PRESSED,
			self.key,self.mouse
		)

		self.player_action = 'didnt-take-turn'
		if self.game_state == 'playing':
			_, result = self.mvkeyhandler(self.key, self)
			if result is not None:
				self.player_action = result

		elif self.game_state == 'selecting':
			_, result = self.selectkeyhandler(self.key, self)

		if self.key.vk == libtcod.KEY_ESCAPE and self.key.lalt:
			self.player_action = 'exit'

		return self.player_action

	def render_all(self):

		libtcod.console_blit(self.con, 0,0, self.SCREEN_WIDTH,self.SCREEN_HEIGHT, 0,0, 0)

		libtcod.console_set_default_background(self.panel, libtcod.black)
		libtcod.console_clear(self.panel)

		#utilities.render_bar(self.panel, 1,1, self.BAR_WIDTH, 'HP',
		#	self.player.fighter.hp,
		#	self.player.fighter.max_hp,
		#	libtcod.red,
		#	libtcod.darker_red
		#)

		#y = 1
		#for line, color in self.game_msgs:
		#	libtcod.console_set_default_foreground(self.panel, color)
		#	libtcod.console_print_ex(self.panel, self.MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
		#	y += 1


		libtcod.console_blit(self.panel, 0,0, self.SCREEN_WIDTH,self.PANEL_HEIGHT, 0,0, self.PANEL_Y)

	def inventory_menu(self, header):
		data = [(item.display_name, item.ident) for item in self.player.get_items()]
		display = [x[0] for x in data]
		index = self.menu(self.con, header, display, self.INVENTORY_WIDTH)

		if index is not None:
			return self.player.get_item(data[index][1])

	def get_names_under_mouse(self):
		x,y = self.mouse.cx, self.mouse.cy
		names = ', '.join(
			obj.name for obj in self.level.iter_objects()

		if
			(obj.x,obj.y) == (x,y)
				and
			self.player.can_see(obj)
		)
		return names.capitalize()



	def menu(self, con, header, options, width):
		if len(options) > 26: raise ValueError('too many items')


		print con
		header_height = libtcod.console_get_height_rect(con, 0,0, width, self.SCREEN_HEIGHT, header)
		height = len(options) + header_height
		window = libtcod.console_new(width, height)

		libtcod.console_set_default_foreground(window, libtcod.white)
		libtcod.console_print_rect(window, 0,0, width,height, header)

		y = header_height
		for option_text in zip('abcdefghijklmnopqrstuvwxyz', options):
			text = '(%s) %s' % option_text
			libtcod.console_print(window, 0, y, text)
			y += 1

		x = self.SCREEN_WIDTH/2 - width/2
		y = self.SCREEN_HEIGHT/2 - height/2
		libtcod.console_blit(window, 0,0, width,height, 0, x,y, 1.0, 0.7)

		key = libtcod.Key()
		mouse = libtcod.Mouse()
		libtcod.console_flush()
		libtcod.sys_wait_for_event(libtcod.KEY_PRESSED, key, mouse, True)

		index = key.c - ord('a')
		if index >= 0 and index < len(options): return index
		return None



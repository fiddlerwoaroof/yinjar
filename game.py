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
	def message(self, msg, color=None):
		if color is None:
			color = libtcod.white
		utilities.message(self.game_msgs, self.MSG_HEIGHT, self.MSG_WIDTH, msg)

	def __init__(self, app_name='test app', screen_width=None, screen_height=None):
		print '__init__'
		if screen_width is None:
			screen_width, screen_height = self.SCREEN_WIDTH, self.SCREEN_HEIGHT
		libtcod.console_init_root(
			screen_width, screen_height, app_name, False
		)

		self.game_msgs = []
		global message
		message = self.message

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

		libtcod.console_blit(self.panel, 0,0, self.SCREEN_WIDTH,self.PANEL_HEIGHT, 0,0, self.PANEL_Y)

	def Inventory_menu(self, header, items):
		data = [(item.display_name, item.ident) for item in items]
		display = [x[0] for x in data]
		index = self.menu(header, display, self.INVENTORY_WIDTH)
		return index, data

	def inventory_menu(self, header):
		index, data = self.Inventory_menu(header, self.player.get_items())
		if index is not None:
			return self.player.get_item(data[index][1])

	def mod_menu(self, header):
		index, data = self.Inventory_menu(header, self.player.get_mods())
		if index is not None:
			return self.player.get_mod(data[index][1])

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



	def menu(self, header, options, width, back_color=libtcod.black, fore_color=libtcod.white):
		import debug
		print '------\n'
		print debug._get_last_module(100)
		print 'menu(', self, header, options, width, back_color, fore_color, ')'
		print '------\n'

		if self.con is None: self.con = 0
		if len(options) > 26: raise ValueError('too many items')

		con = self.con

		header_height = libtcod.console_get_height_rect(con, 0,0, width, self.SCREEN_HEIGHT, header)
		height = len(options) + header_height
		window = libtcod.console_new(width, height)
		print 'window id is:', window
		print

		libtcod.console_set_default_foreground(window, fore_color)
		libtcod.console_print_rect(window, 0,0, width,height, header)

		y = header_height
		for option_text in zip('abcdefghijklmnopqrstuvwxyz', options):
			text = '(%s) %s' % option_text
			libtcod.console_print(window, 0, y, text)
			y += 1

		x = self.SCREEN_WIDTH/2 - width/2
		y = self.SCREEN_HEIGHT/2 - height/2
		libtcod.console_blit(window, 0,0, width,height, 0, x,y, 1.0, 0.9)

		key = libtcod.Key()
		mouse = libtcod.Mouse()
		libtcod.console_flush()
		libtcod.sys_wait_for_event(libtcod.KEY_PRESSED, key, mouse, True)

		libtcod.console_clear(window)
		libtcod.console_blit(window, 0,0, width,height, 0, x,y, 1.0, 0.9)
		libtcod.console_delete(window)
		libtcod.console_flush()

		index = key.c - ord('a')
		if index >= 0 and index < len(options): return index
		return None



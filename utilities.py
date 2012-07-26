import textwrap
import libtcodpy as libtcod

class Rect:
	#a rectangle on the map. used to characterize a room.
	def __init__(self, x, y, w, h):
		self.x1 = x
		self.y1 = y
		self.x2 = x + w
		self.y2 = y + h

	@property
	def width(self):
		return abs(self.x2-self.x1)
	@property
	def height(self):
		return abs(self.y2-self.y1)

	@property
	def center(self):
		return (self.x1+self.x2)/2, (self.y1+self.y2)/2

	@property
	def random_point(self):
		return (
			libtcod.random_get_int(0, self.x1+1, self.x2-1),
			libtcod.random_get_int(0, self.y1+1, self.y2-1)
		)

	def iter_cells(self):
		for x in range(self.x1+1, self.x2):
			for y in range(self.y1+1, self.y2):
				yield x,y

	def intersect(self, other):
		return (
			(self.x1 <= other.x2 and self.x2 >= other.x1)
				and
			(self.y1 <= other.y2 and self.y2 >= other.y1)
		)
	__xor__ = intersect

	def __contains__(self, point):
		x,y = point
		return (
			(self.x1 <= x <= self.x2)
				and
			(self.y1 <= y <= self.y2)
		)


def render_bar(panel, x,y, total_width, name, value, maximum, bar_color, back_color):
	bar_width = int(float(value) / maximum * total_width)
	libtcod.console_set_default_background(panel, back_color)
	libtcod.console_rect(panel, x,y, total_width,1, False, libtcod.BKGND_SET)

	libtcod.console_set_default_background(panel, bar_color)
	if bar_width > 0:
		if bar_width > total_width:
			bar_width = total_width

		libtcod.console_rect(panel, x,y, bar_width,1, False, libtcod.BKGND_SET)

	libtcod.console_set_default_foreground(panel, libtcod.white)
	libtcod.console_print_ex(
		panel, x+total_width/2, y, libtcod.BKGND_NONE, libtcod.CENTER,
		'%s: %s / %s' %(name, value, maximum)
	)

def message(game_msgs, num_msgs, width, new_msg, color=libtcod.white):
	new_msg_lines = textwrap.wrap(new_msg, width)

	for line in new_msg_lines:
		if len(game_msgs) == num_msgs:
			del game_msgs[0]
		game_msgs.append( (line, color) )

class MovementKeyListener(object):
	def __init__(self):
		self.up_cb = None
		self.down_cb = None
		self.right_cb = None
		self.left_cb = None
		self.handlers = {}
		self.char_handlers = {}

	def __call__(self, key, *a, **kw):
		result = None
		if key.vk in self.handlers:
			result = self.handlers[key.vk](*a, **kw) or True
		elif key.c in self.char_handlers:
			result = self.char_handlers[key.c](*a, **kw) or True
		if result is None:
			result = 'didnt-take-turn'
		return (key, result)

	def handle(self, key):
		def _inner(func):
			self.handlers[key] = func
			return self
		if hasattr(key, 'upper'):
			key = ord(key)
			def _inner(func):
				self.char_handlers[key] = func
				return self

		return _inner

	def up(self, func):
		return self.handle(libtcod.KEY_UP)(func)
	def down(self, func):
		return self.handle(libtcod.KEY_DOWN)(func)
	def left(self, func):
		return self.handle(libtcod.KEY_LEFT)(func)
	def right(self, func):
		return self.handle(libtcod.KEY_RIGHT)(func)

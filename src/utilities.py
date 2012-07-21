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
	def center(self):
		return (self.x1+self.x2)/2, (self.y1+self.y2)/2

	@property
	def random_point(self):
		return (
			libtcod.random_get_int(0, self.x1+1, self.x2-1),
			libtcod.random_get_int(0, self.y1+1, self.y2-1)
		)

	def intersect(self, other):
		return (
			(self.x1 <= other.x2 and self.x2 >= other.x1)
				and
			(self.y1 <= other.y2 and self.y2 >= other.y1)
		)
	__xor__ = intersect

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


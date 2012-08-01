import utilities
import math
import libtcodpy as libtcod
import maps

class Object(object):
	# FIXME: map argument unused, remove
	def __init__(self, map, con, x,y, char, name, color, blocks=False, level=None, fighter=None, ai=None, item=None):
		self.name = name
		self.x, self.y = x,y
		self.char = char
		self.color = color
		self.blocks = blocks
		self.con = con
		self.always_visible = False
#		self.map = map

		if level is not None:
			level.add_object(self)
			#level.get_djikstra(x,y)

		self.level = level


		if fighter is not None:
			fighter.owner = self
		self.fighter = fighter

		if ai is not None:
			ai.owner = self
			ai.init(self.level)
		self.ai = ai

		if item is not None:
			item.owner = self
		self.item = item

	@property
	def pos(self):
		return self.x, self.y

	def enter_level(self, level):
		self.level = level
		return self

	def move(self, dx, dy):
		if not self.level.is_blocked(self.x+dx,self.y+dy):
			self.x += dx
			self.y += dy
		else:
			dx,dy = 0,0
		return dx,dy

	def send_to_back(self):
		self.level.send_to_back(self)
		return self

	def distance_to(self, other):
		dx = other.x - self.x
		dy = other.y - self.y
		return math.sqrt(dx**2 + dy**2)

	def distance(self, x,y):
		dx = x - self.x
		dy = y - self.y
		return math.sqrt(dx**2 + dy**2)

	def get_step_towards(self, target_x, target_y):
		dx = target_x - self.x
		dy = target_y - self.y
		distance = math.sqrt(dx**2+dy**2)
		if distance == 0: distance = 1

		dx = int(round(dx/distance))
		dy = int(round(dy/distance))
		return dx,dy

	def move_towards(self, x,y):
		dx,dy = self.get_step_towards(x,y)
		return self.move(dx, dy)

	def draw(self, player=None):
		if player is None or self.always_visible or player.can_see(self.x, self.y):
			libtcod.console_set_default_foreground(self.con, self.color)
			libtcod.console_put_char(self.con, self.x,self.y, self.char, libtcod.BKGND_NONE)
		return self

	def clear(self):
		libtcod.console_put_char(self.con, self.x,self.y, ' ', libtcod.BKGND_NONE)


	def get_visible_objects(cls, fov_map, filter=lambda _: True):
		return [
			object for object in cls.objects
				if filter(object) and libtcod.map_is_in_fov(fov_map, object.x, object.y)
		]

	def get_closest_object(cls, char, *nots, **kwargs):
		filter = kwargs.pop('filter', lambda _: True)
		dist = 100
		cur = None
		for object in cls.level.iter_objects():
			if object is not char and object not in nots and filter(object):
				ndist = char.distance_to(object)
				if ndist < dist:
					dist = ndist
					cur = object
		return cur

	def object_at(self, x,y, filter=lambda _:True):
		for object in self.level.iter_objects():
			if (x,y) == (object.x, object.y) and filter(object):
				return object

	def choose_object(cls):
		names = [
			x.name for x in cls.level.iter_objects() if x is not game.Game.player and x.fighter
		]

		idx = game.menu('Which Monster?', names, max(len(x) for x in names)+10)
		return objects[idx]


import debug


class Fighter(object):
	def __init__(self, hp, defense, power, death_function = None):
		self.death_function = death_function
		self.max_hp = hp
		self.hp = hp
		self.defense = defense
		self.power = power
		self.timers = []

	def heal(self, amount):
		self.hp += amount
		if self.hp > self.max_hp:
			self.hp = self.max_hp

	def stat_adjust(self, time, adjustment_func):
		odefense, opower = self.defense, self.power
		cb, self.defense, self.power = adjustment_func(self.owner)
		self.timers.append(
			(time, self.defense-odefense, self.power-opower, cb)
		)

	def tick(self):
		timers = []
		for timer, ddef, dpow, cb in self.timers:
			timer -= 1
			if timer == 0:
				self.defense -= ddef
				self.power -= dpow
				cb(self.owner)
			else:
				timers.append( (timer,ddef,dpow,cb) )
		self.timers = timers

	def take_damage(self, damage):
		if damage > 0:
			self.hp -= damage

		if self.hp <= 0:
			function = self.death_function
			if function is not None:
				try:
					function(self.owner)
				except TypeError:
					function(self.owner.ai)

	def attack(self, target):
		damage = self.power - target.fighter.defense
		if damage > 0:
			game.message(
				'%s attacks %s for %s hitpoints' % (
					self.owner.name.capitalize(), target.name, str(damage)
				)
			)
			target.fighter.take_damage(damage)
		else:
			game.message(
				'%s attacks but it has no effect' % self.owner.name.capitalize()
			)

from player import Player
import game

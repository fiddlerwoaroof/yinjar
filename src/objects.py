import utilities
import math
import libtcodpy as libtcod
import maps

class Object(object):
	def __init__(self, map, con, x,y, char, name, color, blocks=False, level=None, fighter=None, ai=None, item=None):
		self.name = name
		self.x, self.y = x,y
		self.char = char
		self.color = color
		self.blocks = blocks
		self.con = con
		self.map = map

		if fighter is not None:
			fighter.owner = self
		self.fighter = fighter

		if ai is not None:
			ai.owner = self
		self.ai = ai

		if item is not None:
			item.owner = self
		self.item = item

		if level is not None:
			level.add_object(self)

		self.level = level

	def move(self, dx, dy):
		if not self.map.is_blocked(self.x+dx,self.y+dy):
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

	def move_towards(self, target_x, target_y):
		dx = target_x - self.x
		dy = target_y - self.y
		distance = math.sqrt(dx**2+dy**2)

		dx = int(round(dx/distance))
		dy = int(round(dy/distance))
		return self.move(dx, dy)

	def draw(self, player=None):
		if player is None or player.can_see(self.x, self.y):
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
		for object in cls.level.objects:
			if object is not char and object not in nots and filter(object):
				ndist = char.distance_to(object)
				if ndist < dist:
					dist = ndist
					cur = object
		return cur

	def object_at(cls, x,y, filter=lambda _:True):
		for object in cls.level.objects:
			if (x,y) == (object.x, object.y) and filter(object):
				return object

	def choose_object(cls):
		names = [
			x.name for x in cls.level.objects if x is not game.Game.player and x.fighter
		]

		idx = game.menu('Which Monster?', names, max(len(x) for x in names)+10)
		return objects[idx]


import debug

class Player(Object):
	def __init__(self, map, con, x,y, char, color, fighter=None):
		Object.__init__(self, map, con, x,y, char,
			libtcod.namegen_generate('Celtic male'), color, True, fighter=fighter
		)
		self.fov_recompute = True
		self.fov_map = libtcod.map_new(map.width, map.height)

		self.map.player = self
		self.inventory = []

	def init_fov(self):
		libtcod.map_clear(self.fov_map)
		for x,y,cell in self.level.map.iter_cells_with_coords():
			libtcod.map_set_properties(self.fov_map, x,y,
				not cell.block_sight,
				not cell.blocked
			)

	def draw(self, player=None):
		if player is None:
			player = self
		return Object.draw(self, player)

	def pick_up(self, obj):
		if len(self.inventory) >= 26:
			game.message('Your inventory is full, cannot pick up %s' % obj.name, libtcod.red)
		else:
			self.inventory.append(obj)
			self.level.objects.remove(obj)
			game.message('you picked up a %s!' % obj.name, libtcod.green)
			obj.item.user = self
		return self

	def drop(self, obj):
		self.level.objects.insert(0, obj)
		obj.x, obj.y = self.x, self.y
		game.message('you dropped a %s' % obj.name, libtcod.yellow)

	def use(self, item):
		success = item.use()

		try:
			index = self.inventory.index(item.owner)
		except ValueError:
			index = -1

		if success and index != -1:
			self.inventory.pop(index)

	def get_item(self, index):
		return self.inventory[index].item

	def get_item_names(self):
		return [item.name for item in self.inventory]

	def triggers_recompute(func):
		def _inner(self, *a):
			self.fov_recompute = True
			return func(self, *a)
		return _inner

	def tick(self):
		if self.fighter:
			self.fighter.tick()

	def can_see(self, x,y=None):
		if y is None:
			if hasattr(x, '__iter__'):
				x,y = x
			elif hasattr(x,'x'):
				x,y = x.x,x.y
			else:
				x,y = x.pos

		return libtcod.map_is_in_fov(self.fov_map, x,y)

	fov_algo = libtcod.FOV_DIAMOND
	fov_light_walls = True
	torch_radius = 19

	def recompute_fov(self):
		libtcod.map_compute_fov(
			self.fov_map, self.x, self.y,
				self.torch_radius, self.fov_light_walls, self.fov_algo
		)

		for x,y, cell in self.level.map.iter_cells_with_coords():
			visible = libtcod.map_is_in_fov(self.fov_map, x,y)
			if visible and not cell.explored:
				cell.explored = True

			color = None
			if cell.explored:
				wall = cell.block_sight

				color = {
					True: {True: game.Game.color_light_wall, False: game.Game.color_light_ground},
					False: {True: game.Game.color_dark_wall, False: game.Game.color_dark_ground}
				}[visible][wall]
				libtcod.console_set_char_background(self.con, x, y, color, libtcod.BKGND_SET)



	@triggers_recompute
	def move(self, dx, dy):
		return Object.move(self, dx,dy)

	def move_or_attack(self, dx, dy):
		x = self.x + dx
		y = self.y + dy

		target = None
		for object in self.level.objects:
			if object.fighter and object.x == x and object.y == y:
				target = object
				break

		if target is not None:
			self.fighter.attack(target)
		else:
			self.move(dx, dy)

	def enter_level(self, level):
		self.level = level
		level.enter(self)
		return self

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
				function(self.owner)

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

import game

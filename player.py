import contextlib
import libtcodpy as libtcod
from objects import Object, Fighter
import mods

def get_pos_pair(x,y):
	if y is None:
		if hasattr(x, '__iter__'):
			x,y = x
		elif hasattr(x,'x'):
			x,y = x.x,x.y
		else:
			x,y = x.pos
	return x,y

import collections
class Slot(object):
	def __init__(self):
		self.limit = None
		self.items = []

	@property
	def display_name(self):
		if self.items != []:
			return '%s (x%s)' % (self.items[0].name, len(self.items))

	@property
	def ident(self):
		if self.items != []:
			return self.items[0].name


	def empty(self):
		return len(self.items) == 0

	def _add_item(self, item):
		self.items.append(item)
		return True

	def add_item(self, item):
		result = False
		if self.limit is None or len(self.items) <= self.limit:
			if self.items == []:
				self.limit = item.item.stack_limit
				print 'no items'
				return self._add_item(item)
			elif (len(self.items) < self.limit) and (self.ident == item.name):
				print 'add_items %d' % len(self.items)
				return self._add_item(item)
			elif self.ident != item.name:
				raise ValueError('Cannot stack %s with %s' % (self.ident, item.ident))
		return result

	def get_item(self, default=None):
		result = default
		if self.items != []:
			result = self.items[-1]
		return result

	def consume(self):
		self.items.pop()



class Inventory(object):
	def __init__(self):
		self.objects = {}

	def __iter__(self):
		for v in self.objects.itervalues():
			for i in v:
				yield i

	def __len__(self):
		return sum(len(x) for x in self.objects.values())

	def __contains__(self, it):
		return it.ident in self.objects

	def __getitem__(self, k):
		return self.objects[k][-1].get_item()

	def __setitem__(self, k,v):
		if v.ident != k: raise ValueError('Inventory key must equal the item\'s name')
		self.add_item(v)

	def add_item(self, item):
		print 'add_item', item.name
		slot = self.objects.setdefault(item.name, [Slot()])
		while not slot[-1].add_item(item):
			print 'add slot'
			slot.append(Slot())

	def __delitem__(self, k):
		self.objects[k][-1].consume()
		while self.objects[k] != [] and self.objects[k][-1].empty():
			self.objects[k].pop()
		else:
			if self.objects[k] == []:
				del self.objects[k]

class Player(Object):
	def triggers_recompute(func):
		def _inner(self, *a, **kw):
			self.fov_recompute = True
			return func(self, *a, **kw)
		return _inner

	@triggers_recompute
	def __init__(self, map, con, x,y, char, color, fighter=None, level=None):
		Object.__init__(self, None, con, x,y, char,
			libtcod.namegen_generate('Celtic male'), color, True, fighter=fighter, level=level
		)

		map.player = self
		self.inventory = Inventory()
		self.mods = Inventory()

		class Item:
			stack_limit = 5
		obj = Object(None, con, None,None, 'b', 'boost', color, item=Item())
		obj.mod = mods.Boost()
		self.mods.add_item(obj)

	def draw(self, player=None):
		if player is None:
			player = self
		return Object.draw(self, player)

	def pick_up(self, obj):
		# TODO: limit number of items
		if len(self.inventory) >= 26:
			game.message('Your inventory is full, cannot pick up %s' % obj.name, libtcod.red)
		elif obj is not None:
			self.inventory.add_item(
				self.level.claim_object(obj).item.bind_user(self) # returns item.owner
			)
			game.message('you picked up a %s!' % obj.name, libtcod.green)
		return self

	def drop(self, obj):
		obj = self.inventory[obj.name]
		obj.x, obj.y = self.x, self.y
		self.level.add_object(obj)
		del self.inventory[obj.name]

	def use(self, item):
		item.owner.enter_level(self.level)
		success = item.use()

		if success:
			del self.inventory[item.name]

	@contextlib.contextmanager
	def recategorize_item(self, item_name):
		item = self.inventory[item_name]
		yield item
		del self.inventory[item_name]
		self.inventory.add_item(item)

	def modify(self, item_name, mod_name):
		mod = self.mods[mod_name]
		with self.recategorize_item(item_name) as item:
			item.item.modify(mod.mod)
			del self.mods[mod_name]
		print list(self.mods)

	def unmodify(self, item_name, mod_name):
		with self.recategorize_item(item_name) as item:
			item.item.unmodify(mod_name)
		print list(self.mods)

	def get_mod(self, index):
		return self.mods[index].mod
	def get_mod_names(self):
		return [item.display_name for item in self.mods]
	def get_mods(self):
		return [item for item in self.mods]

	def get_item(self, index):
		return self.inventory[index].item
	def get_item_names(self):
		return [item.display_name for item in self.inventory]
	def get_items(self):
		return [item for item in self.inventory]

	def tick(self):
		if self.fighter:
			self.fighter.tick()

	def can_see(self, x,y=None):
		x,y = get_pos_pair(x,y)
		return self.level.is_visible(x,y)

	torch_radius = 19

	@property
	def pos(self):
		return self.x, self.y
	@pos.setter
	def pos(self, val):
		#print 'pos:', val
		self.x, self.y = val

	@triggers_recompute
	def move(self, dx, dy):
		return Object.move(self, dx,dy)

	def move_or_attack(self, dx, dy):
		x = self.x + dx
		y = self.y + dy

		import monsters
		target = monsters.monster_at(x,y)

		if target is not None:
			self.fighter.attack(target)
		else:
			self.move(dx, dy)

	def enter_level(self, level):
		print '\nenter level\n'
		self.level = level
		level.enter(self)
		self.x, self.y = self.level.map.map_entrance
		return self


import game

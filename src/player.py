import libtcodpy as libtcod
from objects import Object, Fighter

def get_pos_pair(x,y):
	if y is None:
		if hasattr(x, '__iter__'):
			x,y = x
		elif hasattr(x,'x'):
			x,y = x.x,x.y
		else:
			x,y = x.pos
	return x,y

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
		self.inventory = []

	def draw(self, player=None):
		if player is None:
			player = self
		return Object.draw(self, player)

	def pick_up(self, obj):
		if len(self.inventory) >= 26:
			game.message('Your inventory is full, cannot pick up %s' % obj.name, libtcod.red)
		else:
			self.inventory.append(
				self.level.claim_object(obj)
			)
			game.message('you picked up a %s!' % obj.name, libtcod.green)
			obj.item.user = self
		return self

	def drop(self, obj):
		self.level.objects.insert(0, obj)
		obj.x, obj.y = self.x, self.y
		game.message('you dropped a %s' % obj.name, libtcod.yellow)

	def use(self, item):
		item.owner.enter_level(self.level)
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

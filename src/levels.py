import maps
import debug

class Level(object):
	levels = {}

	def register(self, num):
		self.levels[num] = self
		self.number = num
		return self

	def __init__(self, width, height, con, item_types=None, monster_types=None):
		self.objects = []
		self.map = maps.Map(width, height, con, self)

		if item_types is None: item_types = {}
		self.item_types = item_types

		if monster_types is None: item_types = {}
		self.monster_types = monster_types

	def setup(self, max_rooms, min_size, max_size, max_num_monsters, max_num_items):
		self.map.populate_map(
			max_rooms, min_size, max_size,
			self.monster_types, max_num_monsters,
			self.item_types, max_num_items,
		)

	def enter(self, player):
		self.map.enter(player)
		self.player = player
		self.objects.append(player)
		return self

	def add_object(self, obj):
		self.objects.append(obj)
		return self

	def send_to_back(self, obj):
		self.objects.remove(obj)
		self.objects.insert(0,obj)



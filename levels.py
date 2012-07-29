from algorithms import djikstra
import libtcodpy as libtcod
import maps
import debug

class Level(object):
	levels = {}
	color_dark_wall = libtcod.Color(60, 60, 60)
	color_light_wall = libtcod.Color(127,127,127)
	color_dark_ground = libtcod.Color(150,150,150)
	color_light_ground = libtcod.Color(200,200,200)



	def register(self, num):
		self.levels[num] = self
		self.number = num
		return self

	def get_djikstra(self, x,y):
		if (x,y) not in self.djikstra_cache:
			dj = self.djikstra_cache[x,y] = djikstra.DjikstraMap(self.map.map.data)
			dj.set_goals( (x,y), weight=0)
		dj = self.djikstra_cache[x,y]
		dj.cycle()
		return dj

	def __init__(self, width, height, con, item_types=None, monster_types=None):
		self.djikstra_cache = {}
		self.objects = []
		self.map = maps.Map(width, height, con, self)
		self.fov_map = libtcod.map_new(self.map.width, self.map.height)
		self.con = con
		self.player = None

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

	def iter_objects(self):
		return iter(self.objects)

	def add_object(self, obj):
		self.objects.append(
			obj.enter_level(self)
		)
		return obj

	def claim_object(self, obj):
		self.objects.remove(obj)
		return obj

	def enter(self, player):
		#self.map.enter(player)
		if self.player is not None and self.player.level is not None:
			self.player.level.leave(self.player)
		self.player = player
		self.player.pos = self.map.map_entrance
		self.objects.append(player)
		return self

	def leave(self, player):
		#self.map.leave(player)
		self.objects.remove(player)
		self.player = None


	def send_to_back(self, obj):
		self.objects.remove(obj)
		self.objects.insert(0,obj)

	fov_algo = libtcod.FOV_DIAMOND
	fov_light_walls = True
	def recompute_fov(self, clear_all=False):
		x,y = self.map.map_entrance
		if self.player is not None:
			x,y = self.player.pos

		libtcod.map_compute_fov(
			self.fov_map, x,y,
				player.Player.torch_radius, self.fov_light_walls, self.fov_algo
		)

		for x,y, cell in self.map.iter_cells_with_coords():
			visible = libtcod.map_is_in_fov(self.fov_map, x,y)
			if visible and not cell.explored:
				cell.explored = True

			color = libtcod.black
			#if True:
			if cell.explored:
				wall = cell.block_sight
				walkable = not cell.blocked

				if wall or walkable:
					color = {
						True: {True: self.color_light_wall, False: self.color_light_ground},
						False: {True: self.color_dark_wall, False: self.color_dark_ground}
					}[visible][wall]
				elif not walkable:
					color = libtcod.Color(100,100,200)

			if cell.explored or clear_all:
				libtcod.console_set_char_background(self.con, x, y, color, libtcod.BKGND_SET)

	def init_fov(self):
		libtcod.map_clear(self.fov_map)
		#self.fov_map = libtcod.map_new(self.map.width, self.map.height)
		for x,y,cell in self.map.iter_cells_with_coords():
			libtcod.map_set_properties(self.fov_map, x,y,
				not cell.block_sight,
				not cell.blocked
			)

	def is_visible(self, x,y):
		if x < 0 or y < 0:
			raise ValueError(' (%s,%s) not in map ' % (x,y))
		elif x >= self.map.width or y >= self.map.height:
			raise ValueError(' (%s,%s) not in map ' % (x,y))
		return libtcod.map_is_in_fov(self.fov_map, x,y)

	def is_blocked(self, x,y):
		if x < 0 or x > self.map.width:
			result = True
		elif y < 0 or y > self.map.height:
			result = True
		else:
			result = self.map.is_blocked(x,y)
		return result


import game
import player

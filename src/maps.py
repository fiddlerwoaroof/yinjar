import libtcodpy as libtcod
import random
from utilities import Rect

import objects

class Tile(object):
	def __init__(self, blocked, block_sight=None):
		self.blocked = blocked
		self.explored = False
		if block_sight is None:
			block_sight = blocked
		self.block_sight = block_sight


import collections
class Map(collections.MutableSequence):
	def __init__(self, width, height, con, level):
		self.data = [[Tile(True) for y in range(height)
			] for x in range(width)
		]

		self.width = width
		self.height = height
		self.con = con
		self.level = level

	def enter(self, player):
		self.player = player
		return self

	def __iter__(self):
		return iter(self.data)
	def __len__(self):
		return len(self.data)
	def __contains__(self, it):
		return it in self.data
	def __getitem__(self, k):
		return self.data[k]
	def __setitem__(self, k,v):
		return self.data[k][v]
	def __delitem__(self, k):
		del self.data[k]

	def iter_cells_with_coords(self):
		'''NOTE: row is a list, col an instance of Tile'''
		for x,row in enumerate(self):
			for y,cell in enumerate(row):
				yield (x,y,cell)

	def insert(self, *a):
		self.data.insert(*a)

	def populate_map(self, max_rooms, min_size, max_size, monster_types, max_num_monsters, item_types, max_num_items):
		rooms = []
		num_rooms = 0

		for r in range(max_rooms):
			w = random.randrange(min_size, max_size)
			h = random.randrange(min_size, max_size)

			x = random.randrange(0, self.width-w-1)
			y = random.randrange(0, self.height-h-1)

			new_room = Rect(x,y, w,h)

			failed = False
			for other_room in rooms:
				if new_room ^ other_room:
					failed = True
					break

			if not failed:
				self.create_room(new_room)
				(new_x, new_y) = new_room.random_point

				if num_rooms == 0:
					self.player.x, self.player.y = new_room.center

				else:
					self.place_objects(new_room,
						monster_types, max_num_monsters,
						item_types, max_num_items
					)

					prev_x, prev_y = rooms[-1].random_point

					if random.randrange(0,1) == 1:
						self.create_h_tunnel(prev_x, new_x, prev_y)
						self.create_v_tunnel(new_x, prev_y, new_y)
					else:
						self.create_v_tunnel(new_x, prev_y, new_y)
						self.create_h_tunnel(prev_x, new_x, prev_y)

				rooms.append(new_room)
				num_rooms += 1
		return self


	def create_room(self, room):
		for x in range(room.x1+1, room.x2):
			for y in range(room.y1+1, room.y2):
				self[x][y] = Tile(False)

	def create_h_tunnel(self, x1, x2, y):
		for x in range(min(x1,x2), max(x1, x2)+1):
			self[x][y] = Tile(False)

	def create_v_tunnel(self, x, y1, y2):
		for y in range(min(y1,y2), max(y1, y2)+1):
			self[x][y] = Tile(False)

	def is_blocked(self, x,y):
		if self[x][y].blocked:
			return True

		for obj in self.level.objects:
			if obj.blocks and obj.x == x and obj.y == y:
				return True

		return False

	def choose_empty_point(self, room):
		x,y = room.random_point
		while self.is_blocked(x,y):
			x,y = room.random_point
		return x,y

	def place_objects(self, room, monster_types, max_num_monsters, item_types, max_num_items):
		self.place_monsters(room, monster_types, max_num_monsters)
		self.place_items(room, item_types, max_num_items)

	def place_monsters(self, room, monster_types, max_num):
		num_monsters = random.randrange(1, max_num)
		for i in range(num_monsters):
			choice = choose_obj(monster_types)
			if choice:
				x,y = self.choose_empty_point(room)

				choice(self, self.level, self.con, x,y)


	def place_items(self, room, item_types, max_num):
		num_items = random.randrange(0, max_num)
		for i in range(num_items):
			x,y = self.choose_empty_point(room)

			item_type = choose_obj(item_types)
			if item_type:
				objects.Object(self,
					self.con, x,y, item_type.char, item_type.name, item_type.color,

					item=item_type(),
					level=self.level
				).send_to_back()


def choose_obj(chance_dict):
	tot = float(
		sum(chance_dict.values())
	)
	accum = 0
	result = None
	rand = random.randrange(100)
	for choice, chance in chance_dict.items():
		if choice:
			accum += (chance/tot) * 100
			if rand < accum:
				result = choice
				break
	return result


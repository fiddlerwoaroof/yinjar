from __future__ import division
import time
import copy
import libtcodpy as libtcod
import random
from utilities import Rect

try: import numpypy
except ImportError: pass
import numpy as np

import objects

class Tile(object):
	def __init__(self, x,y, blocked, block_sight=None):
		self.blocked = blocked
		self.explored = False
		if block_sight is None:
			block_sight = blocked
		self.block_sight = block_sight



class AutomataEngine(object):
	def __init__(self, width=None, height=None, data=None, randomize=True):
		if data is not None:
			self.data = data
		elif randomize:
			self.data = [ [ random.choice([0]+[1]*3) for y in range(height)] for x in range(width) ]
		else:
			self.data = [ [1 for y in range(height)] for x in range(width) ]
		#self.data = np.array(self.data)
		self.width = width
		self.height = height

	def get_rect(self, p1, p2):
		x1,y1 = p1
		x2,y2 = p2
		x1,x2 = min([x1,x2]), max([x1,x2])
		y1,y2 = min([y1,y2]), max([y1,y2])
		#result = self.data[x1:x2,y1:y2]
		result = [ row[y1:y2] for row in self.data[x1:x2] ]
		return result

	def sum_area(self, p1, p2=None, summator=sum):
		rect = p1
		if isinstance(p2, int):
			x,y = rect
			rect = self.get_rect( (x-p2,y-p2), (x+p2,y+p2) )
		elif p2 is not None:
			rect = self.get_rect(p1,p2)

		return summator( summator(row) for row in rect )

	def iter_with_coords(self):
		for x,row in enumerate(self.data):
			for y,cell in enumerate(row):
				yield x,y,cell

	def munge(self):
		tmp_data = np.array(self.data)

		for x,row in enumerate(self.data):
			for y,cell in enumerate(row):
				tmp_data[x][y] = self.rule(x,y, cell)
		return self.__class__(data=tmp_data)

	def iter(self, num):
		result = self
		for x in range(num):
			result = self.munge()
		return result

	def to_map(self):
		data = [[0]*len(self.data[0]) for _ in self.data]

		for x,y,cell in self.iter_with_coords():
			data[x][y] = Tile(x,y, cell in {1,2}, cell == 1)
		return data

class MazeGen(AutomataEngine):
	def __init__(self, width=None, height=None, data=None, randomize=True, num_rooms=12, max_width=15, max_height=15, **kw):
		kw['randomize'] = False
		AutomataEngine.__init__(self, width, height, data, **kw)


		points = [ (random.randrange(self.width), random.randrange(self.height))
			for _ in range(num_rooms)
		]

		connections = []
		for p in points:
			p2 = random.choice(points)
			while p == p2:
				p2 = random.choice(points)
			connections.append( (p,p2) )

		for p,p2 in connections:
			self.connect_points(p,p2, 9)

		self.rooms = []
		self.expand_rooms(points, max_width, max_height)

	def connect_points(self, p1, p2, steps=4):
		x1,y1 = p1
		x2,y2 = p2
		steps = random.randrange(2, steps+1)

		cx, cy = x1,y1
		h_steps = random.randrange(1,steps) # always at least one vstep
		v_steps = steps - h_steps

		while (cx,cy) != (x2,y2):
			if h_steps > 0 and random.random() < .5:
				dx = int(x2-cx)//(h_steps)
				stop = cx+dx

				a = min([stop,cx])
				b = max([stop,cx])
				for x in range(a,b):
					self.data[x][cy] = 0

				h_steps -= 1

				cx = stop

			elif v_steps > 0:

				dy = int(y2-cy)//(v_steps)
				stop = cy+dy

				a = min([stop,cy])
				b = max([stop,cy])
				for y in range(a,b):
					self.data[cx][y] = 0

				v_steps -= 1
				cy = stop
			elif cx != x2:
				stop = x2
				a = min([stop,cx])
				b = max([stop,cx])
				for x in range(a,b+1):
					self.data[x][cy] = 0
			elif cy != y2:
				stop = y2
				a = min([stop,cy])
				b = max([stop,cy])
				for y in range(a,b+1):
					self.data[cx][y] = 0
			else:
				print 'ouch'
				break

	def expand_rooms(self, points, max_width, max_height):
		for point in points:
			left_offset = random.randrange(int(max_width/2))
			up_offset = random.randrange(int(max_height/2))

			cx, cy = point
			lx, ty = cx-left_offset, cy-up_offset

			if lx < 0:
				max_width += lx
				lx = 0
			if ty < 0:
				max_height += ty
				ty = 0
			w, h = random.randrange(1,max_width+1), random.randrange(1, max_height+1)

			if lx + w >= self.width:
				w -= (lx+w) - self.width
			if ty + h >= self.height:
				h -= (ty+h) - self.height

			print '(',lx,ty, ')', w, h
			room = Rect(lx,ty, w,h)
			success = True
			for o_room in self.rooms:
				success = not o_room ^ room
			if success:
				self.rooms.append(room)

	def rule(self, x,y, cell):
		for room in self.rooms:
			if (x,y) in room:
				return 0
		return cell

	def munge(self):
		tmp_data = np.array(self.data)

		for x,row in enumerate(self.data):
			for y,cell in enumerate(row):
				tmp_data[x][y] = self.rule(x,y, cell)
		return AutomataEngine(data=tmp_data)

class AutomataLoader(AutomataEngine):
	def load_rules(self):
		self.rules = yaml.load(
			file(
				os.path.join('.', 'data', 'mapgenerator.yml')
			)
		)

	def parse_rule(self, rule):
		comp, val = rule.split('->')
		val = val.strip()
		if comp == 'is':
			if val == 'odd':
				return lambda a: (a%2)==1
			elif val == 'even':
				return lambda a: (a%2)==0
			else:
				return lambda a: a == int(val)
		else:
			val = int(val)
			if comp.startswith('>'):
				if comp.startswith('>='):
					return lambda a: a >= val
				return lambda a: a > val

			elif comp.startswith('<'):
				if comp.startswith('<='):
					return lambda a: a <= val
				return lambda a: a < val

			elif comp.startswith('=='):
				return lambda a: a == val

	def rule(self, x,y, cell):
		sum = self.sum_area((x,y), 1)
		for rule in self.rules:
			rule, _, result = rule.partition('::')
			if parse_rule(rule)(cell):
				if hasattr(result, 'upper') and result.lower()=='cell':
					result = cell
				return result

class Automata1(AutomataEngine):
	def rule(self, x,y, cell):
		sum = self.sum_area( (x,y), 1 ) - cell

		if cell == 0 and sum > 3:
			return 0
		elif sum > 5:
			return 1
		elif sum in {2,3}:
			return cell
		else:
			return 0
		#elif sum <= 1:
		#	return 1
		#else:
		#	return cell



class Smoother(AutomataEngine):
	def rule(self, x,y, cell):
		sum = self.sum_area( (x,y), 1 )

		if sum <= 1 and cell == 1:
			return 0
		if sum == 8 and cell == 0:
			return 1
		else:
			return cell

class NewSmoother(AutomataEngine):
	def rule(self, x,y, cell):
		avg = self.sum_area( (x,y), 2 ) / 16
		if avg < .5:
			return 0
		else:
			return 1

import collections
class Map(collections.MutableSequence):
	def __init__(self, width, height, con, level):
		print 'hello again'
		self.gen = MazeGen(width, height)
		self.map = self.data = self.gen.munge()
		#self.data = Automata1(data=self.data.data).iter(2)
		#self.map = Smoother(data=self.data.data).munge()
		self.data = self.map.to_map()

		self.width = width
		self.height = height
		self.con = con
		self.level = level
		self.player = None
		self._map_entrance = None

	@property
	def map_entrance(self):
		if self._map_entrance:
			return self._map_entrance
		else:
			return 0,0
	@map_entrance.setter
	def map_entrance(self, val):
		assert not self.is_blocked(*val)
		self._map_entrance = val

	#def enter(self, player):
	#	self.player = player
	#	return self

	def __iter__(self):
		return iter(self.data)
	def __len__(self):
		return len(self.data)
	def __contains__(self, it):
		return it in self.data
	def __getitem__(self, k):
		return self.data[k]
	def __setitem__(self, k,v):
		self.data[k] = v
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

		print '\n'.join(''.join(map(str, row)) for row in self.map.data)

		for x in range(self.width):
			for y in range(self.height):
				if x in {0,self.width-1} or y in {0,self.height-1}:
					self[x][y].blocked = True
					self[x][y].block_sight = True

		start_room = self.gen.rooms[0]
		x,y = start_room.random_point
		while self.is_blocked(x,y):
			x,y = start_room.random_point
		self.map_entrance = x,y

		self.place_items(self.gen.rooms[0], item_types, max_num_items)
		for r in self.gen.rooms[1:]:
			self.place_objects(r,
				monster_types, max_num_monsters,
				item_types, max_num_items
			)

		return self


	def create_room(self, room):
		for x in range(room.x1, room.x2+1):
			for y in range(room.y1, room.y2+1):
				if x in {room.x1,room.x2} or y in {room.y1,room.y2}:
					self[x][y] = Tile(x,y, True)

	def create_h_tunnel(self, x1, x2, y):
		for x in range(min(x1,x2), max(x1, x2)+1):
			self[x][y] = Tile(x,y, False)

	def create_v_tunnel(self, x, y1, y2):
		for y in range(min(y1,y2), max(y1, y2)+1):
			self[x][y] = Tile(x,y, False)

	def is_blocked(self, x,y):
		if self[x][y].blocked:
			return True

		for obj in self.level.iter_objects():
			if obj.blocks and obj.x == x and obj.y == y:
				return True

		return False

	def choose_empty_point(self, room):
		empty_points = [p for p in room.iter_cells() if not self.is_blocked(*p)]

		result = None,None
		if empty_points:
			result = random.choice(empty_points)

		return result

	def place_objects(self, room, monster_types, max_num_monsters, item_types, max_num_items):
		self.place_monsters(room, monster_types, max_num_monsters)
		self.place_items(room, item_types, max_num_items)

	def place_monsters(self, room, monster_types, max_num):
		num_monsters = random.randrange(1, max_num)
		for i in range(num_monsters):
			choice = choose_obj(monster_types)
			print 'chosen monster: %s' % choice,
			if choice:
				x,y = self.choose_empty_point(room)
				if x is not None and y is not None:
					result = choice(self, self.level, self.con, x,y)
					print result.name, result.fighter.hp, result.fighter.power, result.fighter.defense, x,y,
			print


	def place_items(self, room, item_types, max_num):
		num_items = random.randrange(0, max_num)
		for i in range(num_items):
			item_type = choose_obj(item_types)
			if item_type:
				x,y = self.choose_empty_point(room)
				if x is not None and y is not None:
					self.level.add_object(
						objects.Object(self,
							self.con, x,y, item_type.char, item_type.name, item_type.color,

							item=item_type(),
						)
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


import random
import copy

class DjikstraMap(object):
	def __init__(self, mp=None):
		#print '__init__ djm'
		self.map = None
		if mp is not None:
			self.load_map(mp)

	def load_map(self, mp):
		self.map = [
			[ [255,None][cell] for cell in row ]
				for row in mp
		]
		self.width = len(self.map)
		self.height = len(self.map[0])
	def set_goals(self, *args, **k):
		for x,y in args:
			self.map[x][y] = k.get('weight', 0)

	def iter_map(self):
		for x, row in enumerate(self.map):
			for y, cell in enumerate(row):
				if cell is not None:
					yield (x,y), cell

	def get_cross(self, pos, rad):
		ox,oy = pos
		# up, down, left, right
		result = [
			(ox, oy-rad),
			(ox, oy+rad),
			(ox-rad, oy),
			(ox+rad, oy),
		]
		for idx, (x,y) in enumerate(result):
			if x < 0 or x >= self.width:
				result[idx] = None
			elif y < 0 or y >= self.height:
				result[idx] = None
			else:
				result[idx] = self.map[x][y]
		return result

	def get_rect(self, pos, rad):
		x,y = pos
		result = []
		for cx in range(x-rad, x+rad+1):
			result.append([])
			for cy in range(y-rad, y+rad+1):
				if cx < 0 or cx >= len(self.map):
					result[-1].append(None)
				elif cy < 0 or cy >= len(self.map[0]):
					result[-1].append(None)
				else:
					result[-1].append(self.map[cx][cy])

		return result

	def get_line(self, pos1, pos2):
		x1,y1 = pos1
		x2,y2 = pos2
		if y1 == y2:
			return [ (x,y1) for x in range(x1,x2+1) ]
		if x1 == x2:
			return [ (x1,y) for y in range(y1,y2+1) ]

	def get_borders(self, pos, rad):
		x,y = pos

		results = []
		results.extend(
			self.get_line(
				(min(x-rad, 0), min(y-rad, 0)),
				(min(x-rad, 0), min(y+rad, self.height))
			)
		)
		results.extend(
			self.get_line(
				(min(x-rad, 0),          min(y-rad, 0)),
				(min(x+rad, self.width), min(y-rad, 0))
			)
		)

		results.extend(
			self.get_line(
				(min(x+rad, self.width), min(y+rad, self.height)),
				(min(x-rad, 0),          min(y+rad, self.height))
			)
		)

		results.extend(
			self.get_line(
				(min(x+rad, self.width), min(y+rad, self.height)),
				(min(x+rad, self.width), min(y-rad, 0))
			)
		)

	def iter(self, num):
		result = True
		for _ in range(num):
			result = self.cycle()
			if result == False:
				break
		return result

	def cycle(self):
		changed = False
		out = self.map
		for pos, cell in self.iter_map():
			x,y = pos

			#rect = self.get_rect(pos, 2)
			#neighbors = [n for n in borders(rect)]
			neighbors = (r for r in sum(self.get_rect(pos, 1), []) if r is not None)
			#neighbors = (r for r in self.get_cross(pos, 1) if r is not None)

			try:
				min_neighbor = min(neighbors)
			except ValueError: continue

			if cell > min_neighbor + 1:
				changed = True
				out[x][y] = min_neighbor + 1
		return changed

	def visualize(self):
		print
		for row in zip(*self.map):
			for cell in row:
				if cell is None: print ' ',
				elif cell > 9: print '*',
				else: print cell,
			print

	def get_neighbor_values(self, x,y):
		b = enumerate((enumerate(r,-1) for r in self.get_rect( (x,y), 1 )),-1)
		result = [(i1,i2, v) for i1, r in b for i2,v in r if v is not None]
		#print result
		return result

	def get_low_neighbors(self, x,y, num=2):
		result = sorted(self.get_neighbor_values(x,y), key=lambda a: a[-1])
		return result[:num]

	def categorize(self, values):
		results = {}
		for i1,i2,v in values:
			results.setdefault(v,[]).append( (i1,i2) )
		return results
	def nav(self, x,y):
		results = self.get_neighbor_values(x,y)
		results = self.categorize(results)
		dx,dy = random.choice(results[min(results)])
		#print dx,dy,min(results)

		return dx,dy

def borders(rect):
	mx, my = len(rect)-1, len(rect[0])-1
	for x, row in enumerate(rect):
		for y, cell in enumerate(row):
			if x in {0,mx} or y in {0,my}:
				if cell is not None:
					yield cell

def dist( p1, p2 ):
	x1,y1 = p1
	x2,y2 = p2
	return int( ( (x2-x1)**2+(y2-y1)**2 ) ** .5 )

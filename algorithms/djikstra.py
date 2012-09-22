import random
import copy

try:
	import numpypy as numpy
except ImportError: pass
import numpy

class DjikstraMap(object):
	def __init__(self, mp=None):
		self.goals = []
		self.iters = 0
		#print '__init__ djm'
		self.map = None
		if mp is not None:
			self.load_map(mp)
		self.items = {}

	def __getitem__(self, key):
		return self.map[key]

	def __setitem__(self, key, value):
		x,y = key
		self.map[x,y] = value

	def __iter__(self):
		for x in xrange(self.width):
			for y in xrange(self.height):
				yield (x,y), self[x,y]

	def get_cell(self, x,y=None):
		if y == self.wall:
			x,y = x
		return self[x,y]

	def load_map(self, mp):
		self.width = len(mp)
		self.height = len(mp[0])
		self.max = self.width*self.height
		self.wall = self.width*self.height + 1
		self.map = numpy.array([
			[ [self.max,self.wall][cell] for (y,cell) in enumerate(row) ]
				for (x,row) in enumerate(mp)
		], dtype=numpy.uint64)
		self._set_goals()

	def set_goals(self, *args, **k):
		self.goals.extend(args)

	def _set_goals(self):
		for x,y in self.goals:
			self[x,y] = 0

	def get_cost(self, pos):
		while self[pos] != min_neighbor+1 and self.cycle():
			pass
		return self[pos]

	def iter_map(self):
		wall = self.wall
		for idx, cell in enumerate(self.map.flat):
			if cell == self.wall: continue
			h = self.height
			x,y = idx // h, idx % h
			#assert cell == self.map[x,y], "%s %s %s != %s" % (x,y, cell, self[x,y])
			yield (x,y), cell

	def iter_map(self):
		return (
			( (x,y), self[x,y] )
				for x in xrange(self.width)
				for y in xrange(self.height)
				if self[x,y] != self.wall
		)

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
				result[idx] = self[x,y]
		return result

	def get_rect(self, pos, rad):
		x,y = pos
		lx = max(x-rad,0)
		ty = max(y-rad,0)
		end = rad+1
		#print (x,y), end, (lx, ty) ,(x+end,y+end)
		result = self.map[lx:x+end,ty:y+end]
		return result

	def get_line(self, pos1, pos2):
		x1,y1 = pos1
		x2,y2 = pos2
		if y1 == y2:
			return [ (x,y1) for x in range(x1,x2+1) ]
		if x1 == x2:
			return [ (x1,y) for y in range(y1,y2+1) ]

	def iter(self, num):
		result = True
		for _ in range(num):
			result = self.cycle()
			if result == False:
				break
		return result

	def closest_goal(self, pos):
		return min( (g for g in self.goals), key=lambda g: dist(g,pos) )

	def cycle(self):
		goals = self.goals[:]
		for i in range(1,max(self.width,self.height)):
			for (x,y) in goals:
				neighbors = self.get_rect( (x,y), i )
				neighbors[(neighbors >= i) & (neighbors != self.wall)] = i
		return False

	def cycle1(self):
		t0 = time.time()
		changed = False
		out = self.map
		for pos, cell in self.iter_map():
			x,y = pos

			#print
			neighbors = self.get_rect(pos,1)

			#print pos, cell == self.max, cell==self.wall, cell == 0
			#print neighbors

			if len(neighbors[0]) == 0:
				print 'ack'
				continue
			#for l in neighbors:
			#	print (x,y), l
			#print

			min_neighbor = numpy.min(neighbors)

			if cell > min_neighbor + 1:
				self[x,y] = min_neighbor + 1
				changed = True

			#if cell > min_neighbor + 1:
			#	changed = True
			#	self[x,y] = min_neighbor + 1

		if changed:
			self.iters += 1
		return changed

	def visualize(self):
		print
		out = []
		for x in range(self.width):
			out.append([])
			for y in range(self.height):
				cell = self[x,y]
				if cell == self.wall: out[-1].append(' ')
				elif cell == self.max: out[-1].append('x')
				elif cell > 9: out[-1].append('*')
				else: out[-1].append(str(cell))
		print '\n'.join(''.join(x) for x in zip(*out))

	def get_neighbor_values(self, x,y):
		b = enumerate((enumerate(r,-1) for r in self.get_rect( (x,y), 1 )),-1)
		result = [(i1,i2, v) for i1, r in b for i2,v in r if v != self.wall]
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

	def borders(self, rect):
		mx, my = len(rect)-1, len(rect[0])-1
		for x, row in enumerate(rect):
			for y, cell in enumerate(row):
				if x in {0,mx} or y in {0,my}:
					if cell != self.wall:
						yield cell

def dist( p1, p2 ):
	x1,y1 = p1
	x2,y2 = p2
	return int( ( (x2-x1)**2+(y2-y1)**2 ) ** .5 )

if __name__ == '__main__':
	import random
	width, height = 199,50
	#map = [ [ random.choice([1,0,0,0,0]) for _ in range(height) ] for __ in range(width) ]
	import sys

	out = []
	for line in sys.stdin:
		out.append( [ int(x) for x in line.strip() ] )
	map = out
	width, height = len(map), len(map[0])



	import time
	goals = [ (random.randrange(width), random.randrange(height)) for _ in range(5) ]
	ot = time.time()
	for _ in range(3):
		print '\tinit'
		t0 = time.time()
		dj = DjikstraMap()
		dj.set_goals(*goals)
		dj.load_map(map)
		#dj.iter(10)
		while dj.cycle():
			pass
			#print 'c'
			#dj.visualize()
			#print
		t = time.time() - t0
		print '\tdone', t, 'iters', dj.iters
	print time.time() - ot
	dj.visualize()


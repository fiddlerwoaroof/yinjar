import random
from main import Game
import game
import objects
import libtcodpy as libtcod
import items

from main import game_instance
from algorithms import djikstra

class Monster(object):
	def init(self,*a): pass
	def take_turn(self): pass
	def load_data(self, data):
		for k,v in data.items():
			setattr(self, k,v)
		return self

class BasicMonster(Monster):
	def take_turn(self):
		monster = self.owner
		if game_instance.player.can_see(monster.x, monster.y):
			if monster.distance_to(game_instance.player) > 1:
				dx,dy = monster.move_towards(game_instance.player.x, game_instance.player.y)
				counter = 0
				while (dx,dy) == (0,0) and counter < 10: # wiggle around if stuck
					counter += 1
					dx,dy = monster.move(random.randrange(-1,2,2), random.randrange(-1,2,2))
				#print 'wiggled %s times' % counter
			elif game_instance.player.fighter.hp > 0:
				monster.fighter.attack(game_instance.player)

class Thief(BasicMonster):
	def init(self, level):
		self.level = level
		self.player = level.player
		self.inventory = []
		self.skill = self.skill / 100.0

	def take_turn(self):
		if self.player.distance(self.owner.x, self.owner.y) < 2 and random.random() < .7:
			self.steal()
		else:
			BasicMonster.take_turn(self)

	def steal(self):
		if self.player.inventory.keys():
			print self.player.inventory.keys()
			game_instance.message( ('%s can\'t find anything to steal'%self.owner.name).capitalize(), libtcod.orange )
			obj = random.choice(self.player.inventory.keys())
			game_instance.message( ('%s tries to steal %s'%(self.owner.name,obj)).capitalize(), libtcod.red)
			if random.random() < self.skill:
				game_instance.message( ('%s successfully steals %s'%(self.owner.name,obj)).capitalize(), libtcod.orange)
				obj = self.player.inventory[obj]
				self.inventory.append(obj)
				del self.player.inventory[obj.name]

	def death(self):
		monster_death(self.owner)
		for item in self.inventory:
			self.drop(item)

	def drop(self, item):
		item.x, item.y = self.owner.pos
		self.level.add_object(item)
		self.inventory.remove(item)


class DjikstraMonster(Monster):
	maps = {}

	@property
	def dj(self):
		result = self.maps.get(id(self.level))
		if result is None:
			result = self.maps[id(self.level)] = djikstra.DjikstraMap()
		return result

	def init(self, level):
		self.level = level
		self.owner.always_visible = True

		self.opos = self.owner.x, self.owner.y
		self.ppos = None

		map = level.map
		#self.dj.visualize()

	def take_turn(self):
		pos = self.owner.x, self.owner.y

		dx,dy = 0,0
		if self.level.is_visible(*pos):
			if self.level.player.distance(*pos) < 2:
				self.owner.fighter.attack(game_instance.player)
			else:
				dx, dy = self.owner.move_towards(*self.level.player.pos)

		#elif random.random() < .4:
		#	dx,dy = self.dj.nav(*pos)

		else:
			dj = self.level.get_djikstra(*self.level.player.pos)
			#print pos, '<---', self.level.player.distance(*pos)
			x,y = pos
			dx,dy = dj.nav(x,y)

		self.owner.move(dx,dy)




class AdvancedMonster(Monster):
	def perimeter(self, rect):
		for dx,row in enumerate(rect, -1):
			for dy, cell in enumerate(row, -1):
				if (dx in {-1,1}) or (dy in {-1,1}):
					yield dx,dy, cell
	def take_turn(self):
		monster = self.owner
		if not game_instance.player.can_see(monster.x, monster.y):
			return
		elif monster.distance_to(game_instance.player) > 1:
			x,y = monster.x, monster.y
			player_x, player_y = game_instance.player.pos
			neighborhood = [ [0,0,0], [0,0,0], [0,0,0] ]
			for dx in range(-1,2):
				for dy in range(-1,2):
					new_x = x+dx
					new_y = y+dy
					neighborhood[dx+1][dy+1] += int(monster.level.is_blocked(x+dx, y+dy))
			dx, dy = monster.get_step_towards(player_x, player_y)
			if neighborhood[dx+1][dy+1]:
				open = []
				for dx,dy, cell in self.perimeter(neighborhood):
					if not cell:
						open.append( (dx,dy) )
				open = sorted(open, key=lambda (a,b): abs(a-dx)+abs(b-dy))[:3]
				dx,dy = random.choice(open)
			monster.move(dx,dy)
		else:
			monster.fighter.attack(game_instance.player)


class ConfusedMonster(Monster):
	def __init__(self, num_turns=game_instance.CONFUSE_NUM_TURNS):
		self.num_turns = num_turns

	def attach(self, object):
		self.old_ai = object.ai
		self.owner = object
		object.ai = self

	def take_turn(self):
		if self.num_turns > 0:
			game.message('%s is confused' % self.owner.name)
			op = get_closest_monster(self.owner, game_instance.player)
			if self.owner.distance_to(op) >= 2:
				self.owner.move_towards(op.x, op.y)
			else:
				game.message('%s attacks %s in his confusion' % (self.owner.name, op.name))
				if self.owner.fighter:
					self.owner.fighter.attack(op)
				if op.fighter:
					op.fighter.attack(self.owner)

			self.num_turns -= 1
		else:
			self.owner.ai = self.old_ai
			game.message('%s is no longer confused' % self.owner.name)

def monster_death(monster):
	monster.char = '\x09'
	monster.color = libtcod.dark_red
	monster.blocks = False
	monster.fighter = None
	monster.ai = None
	monster.name = 'remains of %s' % monster.name
	monster.send_to_back()


import functools
monster_at = functools.partial(game_instance.player.object_at,
	filter=lambda obj: obj.fighter and obj is not game_instance.player
)

get_closest_monster = functools.partial(game_instance.player.get_closest_object,
	filter=lambda obj: obj.fighter
)

get_visible_monsters = functools.partial(game_instance.player.get_visible_objects,
	filter=lambda obj: obj.fighter
)


#####

import yaml
import os.path
import glob
import monsters
class MonsterLoader(object):
	def __init__(self, dir):
		self.dir = dir

	def load_monsters(self):
		for fn in glob.glob(os.path.join(self.dir,'*.yml')):
			print 'fn', fn
			for doc in yaml.safe_load_all(file(fn)):
				self.load_monster(doc)

	def load_monster(self, doc):
		color = doc.get('color', None)
		if color is None:
			color = libtcod.red
		elif hasattr(color, 'upper'):
			color = getattr(libtcod, color)
		else:
			color = libtcod.Color(*color)

		ai_class = doc.get('ai_class', BasicMonster)
		cls_data = {}
		if ai_class is not BasicMonster:
			cls_data = {}
			if hasattr(ai_class, 'items'):
				nm = ai_class.pop('class_name', 'monsters.BasicMonster')
				cls_data.update(ai_class)
				ai_class = nm

			module, clas = ai_class.rsplit('.',1)
			module = __import__(module)
			ai_class = getattr(module, clas)

		death_func = getattr(ai_class, 'death', monster_death)

		print 'loading', doc
		Game.register_monster_type(
			(lambda doc:
				lambda map,level,con,x,y: objects.Object( map, con, x,y,
					doc['char'],
					doc.get('name_fmt', '%s the %s') % (
						libtcod.namegen_generate(doc['namegen_class']).capitalize(),
						doc['race_name'].capitalize()
					),
					color,
					True,
					fighter=objects.Fighter(
						hp=doc['hp'],
						defense=doc['defense'],
						power=doc['power'],
						death_function=monster_death
					),
					ai=ai_class().load_data(cls_data),
					level=level
				)
			)(doc), doc['spawn_chance'])

Game.register_monster_type(
	lambda map,level, con,x,y: objects.Object(map, con,
		x,y, '\x02', '%s the Orc' % libtcod.namegen_generate('Fantasy male'),
			libtcod.blue, True,

		fighter=objects.Fighter(hp=10, defense=2, power=3, death_function=monster_death),
		ai=AdvancedMonster(),
		level=level
), 8)

Game.register_monster_type(
	lambda map,level, con,x,y: objects.Object(map, con,
		x,y, '\x01', '%s the Troll' % libtcod.namegen_generate('Norse male'),
			libtcod.orange, True,

		fighter=objects.Fighter(hp=16, defense=1, power=4, death_function=monster_death),
		ai=AdvancedMonster(),
		level=level
), 2)

Game.register_monster_type(
	lambda map,level, con,x,y: objects.Object(map, con,
		x,y, '\x01', '%s the Olog-Hai' % libtcod.namegen_generate('Norse male'),
			libtcod.amber, True,

		fighter=objects.Fighter(hp=16, defense=1, power=7, death_function=monster_death),
		ai=BasicMonster(),
		level=level
), 1)
Game.register_monster_type(None, 7)


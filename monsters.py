import random
from main import Game
import game
import objects
import libtcodpy as libtcod
import items

from main import game_instance

class Monster(object):
	def take_turn(self): pass

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
				print 'wiggled %s times' % counter
			elif game_instance.player.fighter.hp > 0:
				monster.fighter.attack(game_instance.player)

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
		if ai_class is not BasicMonster:
			module, clas = ai_class.rsplit('.',1)
			module = __import__(module)
			ai_class = getattr(module, clas)

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
					ai=ai_class(),
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
		ai=AdvancedMonster(),
		level=level
), 1)
Game.register_monster_type(None, 7)


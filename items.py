from __future__ import division
import os.path
import glob
import yaml

import libtcodpy as libtcod
import game
import objects
import utilities
import monsters
import random
from main import Game


class Item(object):
	stack_limit = 5
	def __init__(self, stackable=False):
		self.stacks_with = []

	def __new__(*args):
		res = object.__new__(*args)
		return res
	def bind_game(self, game):
		self.game = game
	def bind_user(self, user):
		self.user = user
		return self.owner
	def free_user(self):
		self.user = None
		return self.owner

class ItemLoader(object):
	def __init__(self, dir):
		self.dir = dir

	def load_items(self):
		for fn in glob.glob(os.path.join(self.dir,'*.yml')):
			print 'fn', fn
			for doc in yaml.safe_load_all(file(fn)):
				self.load_item(doc)

	def load_item(self, doc):
		_color = doc.get('color', None)
		if _color is None:
			_color = libtcod.green
		elif hasattr(_color, 'upper'):
			_color = getattr(libtcod, _color)
		else:
			_color = libtcod.Color(*_color)

		item_class = doc['item_class']
		module, clas = item_class.rsplit('.',1)
		module = __import__(module)
		item_class = getattr(module, clas)
		print 'item class:', item_class

		print 'loading', doc
		@Game.register_item_type(doc['spawn_chance'])
		class LoadedItem(item_class):
			name = doc.get('item_description')
			char = doc.get('char', '!')
			color = _color
			stack_limit = doc.get('stack_limit', Item.stack_limit)
			stacks_with = doc.get('stacks_with', ())


@Game.register_item_type(5)
class HealingPotion(Item):
	name = 'Healing potion'
	char = '\x03'
	color = libtcod.violet
	def use(self):
		fighter = self.user.fighter

		result = True
		if fighter.hp == fighter.max_hp:
			self.game.message('You\'re full, can\'t heal', libtcod.red)
			result = False
		else:
			self.game.message('Healing...')
			fighter.heal(10)

		return result

@Game.register_item_type(2)
class SuperHealingPotion(Item):
	name = 'Super healing potion'
	char = '\x03'
	color = libtcod.yellow
	def use(self):
		fighter = self.user.fighter
		if random.random() < .75:
			fighter.max_hp += 10
			fighter.heal(10)
		return True

@Game.register_item_type(1)
class Confusion(Item):
	name = 'Confusion'
	char = 'c'
	color=libtcod.dark_chartreuse
	def use(self):
		monster = monsters.get_closest_monster(self.user)

		result = False
		if monster is not None:
			self.game.message('%s becomes confused' % monster.name)
			monsters.ConfusedMonster(random.randrange(10,18)).attach(
				monster
			)
			result = True

		return result

@Game.register_item_type(4)
class Strengthen(Item):
	name = 'Strengthen'
	char = 's'
	color = libtcod.chartreuse
	def use(self):
		if self.user.fighter:
			self.game.message('%s feels a surge of strength' % self.user.name)
			self.user.fighter.stat_adjust(20, self.adj)
		return True

	def adj(self, owner):
		return (
			lambda _: self.game.message('The surge of strength has subsided'),
			owner.fighter.defense,
			owner.fighter.power+3
		)

@Game.register_item_type(4)
class Protect(Item):
	name = 'Protect'
	char = 'p'
	color = libtcod.chartreuse
	def use(self):
		if self.user.fighter:
			self.game.message('%s is surrounded by a protecting aura' % self.user.name)
			self.user.fighter.stat_adjust(15, self.adj)
		return True

	def adj(self, owner):
		return (
			lambda _: self.game.message('The protecting aura dissipates'),
			owner.fighter.defense+6,
			owner.fighter.power
		)

@Game.register_item_type(2)
class LightningBolt(Item):
	name = 'Lightning Bolt'
	char = 'z'
	color = libtcod.darkest_red
	def use(self):
		monster = monsters.get_closest_monster(self.user)
		result = False
		if monster and self.user.can_see(monster.x, monster.y):
			self.game.message('Monster %s has been struck by lightning' % monster.name)
			monster.fighter.take_damage(13)
			result = True
		else:
			self.game.message('No target')
		return result

@Game.register_item_type(5)
class Jump(Item):
	name = 'Jump'
	char = 'j'
	color= libtcod.dark_green
	jump_distance = 3
	def use(self):
		self.game.select(self.jump)
		return True
	def jump(self, x,y):
		dist = self.user.distance(x,y)

		if dist <= self.jump_distance:
			self.user.x, self.user.y = x,y
			self.game.message('you are transported to a new place')
		elif random.random() < self.jump_distance/dist:
			self.user.x, self.user.y = x,y
			self.game.message('you strain all your power to move %d squares' % int(dist))
		else:
			self.game.message('you didn\'t make it')
			self.user.fighter.take_damage( int(round(2 * dist/self.jump_distance)) )

@Game.register_item_type(3)
class Acquire(Item):
	name = 'Acquire'
	char = 'a'
	color= libtcod.dark_green
	effect_distance = 5
	def use(self):
		self.game.message('what do you want?')
		self.game.select(self.get)
		return True
	def get(self, x,y):
		if self.user.distance(x,y) < self.effect_distance:
			self.user.pick_up(self.user.object_at(x,y))


@Game.register_item_type(1)
class Smite(Item):
	name = 'Smite'
	char = '\x0f'
	color = libtcod.red
	def use(self):
		self.game.select(self.smite)
		return True

	def smite(self, x,y):
		monster = monsters.monster_at(x,y)
		if monster:
			monster.fighter.take_damage(10)
			if monster.fighter:
				self.game.message('%s is smitten, he only retains %s hp' % (monster.name, monster.fighter.hp))
			else:
				self.game.message('%s thought it better to go elsewhere' % monster.name)


@Game.register_item_type(2)
class Fireball(Item):
	name = 'Fireball'
	char = '*'
	color = libtcod.darker_red
	effect_radius = 5

	def use(self):
		self.game.select(self.smite)
		return True

	def smite(self, x,y):
		if random.random() < .1:
			self.effect_radius *= 2

		strikes = []
		for obj in self.owner.level.objects:
			if obj.fighter and obj is not self.user:
				if (obj.x, obj.y) == (x,y):
					self.game.message('%s takes a direct hit from the fireball' % obj.name)
					obj.fighter.take_damage(20)
				elif obj.distance(x,y) < self.effect_radius:
					obj.fighter.take_damage(6)
					if obj.fighter:
						strikes.append('%s %s' % (obj.name, obj.fighter.hp))
					else:
						strikes.append('%s dead' % obj.name)
		self.game.message('The names of those who were to close for comfort: %s' % ', '.join(strikes))


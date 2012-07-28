
class Weapon(object):
	def __init__(self, power_boost=0, chance_to_hit=100):
		self.power_boost = power_boost
		self.chance_to_hit = chance_to_hit

		self.ammo = []
		self.mods = []
		self.user = None

	def modify(self, mod):
		if mod.modify(self):
			self.mods.append(mod)
	def remove_mod(self, mod):
		if mod.undo(self):
			self.mods.remove(mod)

	def load(self, ammo):
		self.ammo.append(ammo)

	def equip(self, user):
		self.user = user

	def attack(self, target):
		pass


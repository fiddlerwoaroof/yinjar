import math
class Mod(object):
	'''An undoable change to some object or item'''

	def __init__(self):
		pass

	def modify(self, target):
		pass

	def revert(self, target):
		pass

class Boost(Mod):
	name = 'boost'

	def modify(self, target):
		target.potency *= 1.5
		result = math.ceil(target.potency)
		target.potency = int(result)
		target.name = 'boosted %s' % target.name
	def revert(self, target):
		target.potency /= 1.5
		result = math.ceil(target.potency)
		target.potency = int(result)
		target.name = target.name.split(' ', 1)[1]


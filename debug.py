import inspect
import os
def take(num, iter_):
   for _ in range(num): yield iter_.next()

def get_last_module(num=1, exclude_modules={'debug'}):
	modname = '%s.py' % __name__.split('.')[-1]
	try:
		result = take(
			num,
			(x for x in
					((b.split(os.path.sep)[-1], a.f_lineno)
						for (a,b,c,d,e,f) in inspect.getouterframes(inspect.currentframe())
					)
			)
		)
	except:
		result = [('Unknown Output',-1)]
	result = [ [str(y) for y in x] for x in result]
	if num == 1:
		result = result[0]
	return result

def debug(func):
	def _inner(*a,**kw):
		try:
			result = func(*a,**kw)
		except Exception, e:
			result = 'raised %s' % e
			raise
		else:
			result = 'returned %s' % result
		finally:
			print '%s args:%s kwargs:%s finished and %s' % (func,a,kw,result)
		return result
	return _inner

_get_last_module = get_last_module

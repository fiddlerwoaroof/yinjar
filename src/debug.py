import inspect
import os
def take(num, iter_):
   for _ in range(num): yield iter_.next()

def _get_last_module(num=1, exclude_modules={'debug'}):
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


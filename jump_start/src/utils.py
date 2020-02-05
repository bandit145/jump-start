import os

def prep_local():
	user = os.getenv('USER')
	if not os.path.isdir('/home/'+ user + '/.jump-start/'):
		os.mkdir('/home/'+ user + '/.jump-start/')
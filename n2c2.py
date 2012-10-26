# Author: Fletcher Moore
# contributors: Tiago Barroso
# this software is public domain.
from n2c2lib.NotesToCards import NotesToCards        
		
app = NotesToCards()
try:
	# if Anki is found, we are an Anki addon
	import anki 
	app.runAsAnkiPlugin()
except ImportError:
	# not anki addon, run from command line
	app.makeFromOdt('gdocs.odt')
	#print 'no way to run from command line right now...'


# not the best way to do imports?


from n2c2lib.RawCard import RawCard
from n2c2lib.OdtModel import OdtModel

from n2c2lib.CardBuilder import CardBuilder
from n2c2lib.debug import debug
import re, os, constants, json


class NotesToCards():
	
	# called once when app is created
	def configure(self, args):
		self.isJsonMode = args.json
		self.isTextMode = args.text
		self.inputFile = args.file
		self.outputFile = args.out
	
	# called once after app is created
	def execute(self):
		if self.isJsonMode:
			print 'this feature is currently unavailable'
			#self.dumpJson()
		else:
			self.makeFromOdt(self.inputFile, '.')
			self.dumpToFile(self.outputFile)
		
		
	# called by anki plugin, command line
	# todo: eliminate mediaPath by fixing imageTracker
	def makeFromOdt(self, filePath, mediaPath):
		odt = OdtModel(filePath, mediaPath)
		self.paths = odt.getPaths()
		
		cardBuilder = CardBuilder()
		self.cards = cardBuilder.build(self.paths)
		
		return len(self.cards)
		
				
	def dumpToFile(self, out = 'test.txt'):
		path = 'test.txt' # needs fixing for command line implementation
		f = open(path, 'w')
		for c in self.cards:
			f.write(c.asTabDelimited())
		f.close()

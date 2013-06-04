
# not the best way to do imports?


from n2c2lib.RawCard import RawCard
from n2c2lib.OdtModel import OdtModel

from n2c2lib.CardBuilder import CardBuilder
from n2c2lib.debug import debug
import re, os, constants, json


# how much jank?
def rreplace(text, old, new, count):
	return text[::-1].replace(old[::-1], new[::-1], count)[::-1]
	

class NotesToCards():
	
	def __init__(self):
		self.isAnkiPlugin = False
		

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
			self.makeFromOdt(self.inputFile)
			self.dumpToFile(self.outputFile)
		
	def discardDuplicates(self, theList):
		uniqueItems = []
		for item in theList:
			try:
				uniqueItems.index(item)
			except:
				uniqueItems.append(item)
		return uniqueItems
	
	def dumpPaths(self, indexes):
		for i in indexes:
			print '\t', self.paths[i]			
	
		
	def makeCardsFromPaths(self):
		cardBuilder = CardBuilder()
		self.cards = cardBuilder.build(self.paths)		
		
	
	# returns number of cards created or None if no file is read.
	# called by anki plugin
	# todo: eliminate mediaPath by fixing imageTracker
	def makeFromOdt(self, filePath, mediaPath):
		odt = OdtModel(filePath, mediaPath)
		self.paths = odt.getPaths()
		
		cardBuilder = CardBuilder()
		self.cards = cardBuilder.build(self.paths)
		
		return len(self.cards)

	def dumpJson(self):
		self.builder.isTextMode = self.isTextMode # configuration is getting terrible
		self.makePathsFromFile(self.inputFile)
		trees = []
		for node in self.trees:
			trees.append(node.asJson())
		print json.dumps(trees)
		self.imageTracker.cleanup() # must be called to remove the temporary directory
		
				
	def dumpToFile(self, out = 'test.txt'):
		path = 'test.txt' # needs fixing for command line implementation
		f = open(path, 'w')
		for c in self.cards:
			f.write(c.asTabDelimited())
		f.close()

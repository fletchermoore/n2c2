
# not the best way to do imports?
from zipfile import ZipFile, is_zipfile
from n2c2lib import ElementTree as etree
from n2c2lib.RawCard import RawCard
from n2c2lib.ImageTracker import ImageTracker
from n2c2lib.TextBuilder import TextBuilder 
from n2c2lib.Style import Style
from n2c2lib.debug import debug
from n2c2lib.Node import Node
import re, os, StringIO, constants, json


# how much jank?
def rreplace(text, old, new, count):
	return text[::-1].replace(old[::-1], new[::-1], count)[::-1]
	
# stolen from someone else on stackoverflow
def parse_and_get_ns(file):
  events = "start", "start-ns"
  root = None
  ns = {}
  for event, elem in etree.iterparse(file, events):
    if event == "start-ns":
      if elem[0] in ns and ns[elem[0]] != elem[1]:
        # NOTE: It is perfectly valid to have the same prefix refer
        #   to different URI namespaces in different parts of the
        #   document. This exception serves as a reminder that this
        #   solution is not robust.  Use at your own peril.
        raise KeyError("Duplicate prefix with different URI found.")
      ns[elem[0]] = "%s" % elem[1]
    elif event == "start":
      if root is None:
        root = elem
  return etree.ElementTree(root), ns
  

class NotesToCards():
	
	def __init__(self):
		self.isAnkiPlugin = False
		self.destDir = '.'
		self.reset()
	
	def reset(self):
		self.inputFile = None
		self.outputFile = None
		self.isJsonMode = False
		self.isTextMode = False
		self.paths = []
		self.trees = []
		self.indexesToIgnore = []
		self.cards = []
		self.prevCard = RawCard('', '', 1)
		self.styles = []
		self.names = {}
		# maybe make imageTracker TextBuilder only
		self.imageTracker = ImageTracker()
		self.imageTracker.destPath = self.destDir
		self.builder = TextBuilder()
		self.builder.imageTracker = self.imageTracker
		self.builder.destPath = self.destDir # is this necessary?
	
	# called once when app is created
	def configure(self, args):
		self.isJsonMode = args.json
		self.isTextMode = args.text
		self.inputFile = args.file
		self.outputFile = args.out
	
	# called once after app is created
	def execute(self):
		if self.isJsonMode:
			self.dumpJson()
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
	
	# returns a subset of self.paths that match the given path
	# up to the final index
	def getMatchingSubset(self, givenPath, finalIndex):
		indexes = []
		for pathIndex in range(len(self.paths)):
			for nodeIndex in range(len(self.paths[pathIndex])):
				if nodeIndex > finalIndex:
					indexes.append(pathIndex)
					break
				if self.paths[pathIndex][nodeIndex] != givenPath[nodeIndex]:
					break
		return indexes
	
	# removes the force tag from the given paths at the given depth	
	def removeForce(self, indexes, depth):
		for i in indexes:
			self.paths[i][depth] = self.paths[i][depth].replace('{{force}}', '')
	
	def makeCardFromSubset(self, indexes, backIndex):
		uniqueBacks = []
		for i in indexes:
			maybeBack = self.paths[i][backIndex]
			try:
				uniqueBacks.index(maybeBack)
			except:
				uniqueBacks.append(maybeBack)
		
		num = len(uniqueBacks)
		back = constants.htmlBr.join(uniqueBacks)
		back = re.sub(r'{{.+?}}', '', back)
		#print 'back// ', back
		
		# any of the paths should do, since they should all start the same
		frontPath = self.paths[indexes[0]][:backIndex]
		front = self.makeFront(frontPath)
		if num > 1:
			front += ' (%d)' % num
		#print 'front// ', front
		
		self.cards.append(RawCard(front, back, 1))
		
	def addIgnores(self, indexes, length):
		for i in indexes:
			#print len(self.paths[i]), length
			if (len(self.paths[i]) == length):
				#print 'to be REMOVED ', self.paths[i]
				self.indexesToIgnore.append(i)
		
	def dumpPaths(self, indexes):
		for i in indexes:
			print '\t', self.paths[i]			
	
	# return true to continue making the card after dealing with the
	# forced list
	def checkForForce(self, path):
		nodeIndex = 0
		for node in path:
			if node.find('{{force}}') > -1:
				#print 'force FOUND in ', nodeIndex
				matchingIndexes = self.getMatchingSubset(path, nodeIndex)
				self.removeForce(matchingIndexes, nodeIndex)
				self.makeCardFromSubset(matchingIndexes, nodeIndex+1)
				self.addIgnores(matchingIndexes, nodeIndex+2)
				# check to see if the current card was added to the ignore list
				# if it was, do not continue with card creation
				currentIndex = self.paths.index(path) # this should never fail
				try:
					self.indexesToIgnore.index(currentIndex)
					return False # do not continue
				except:
					return True # not ignoring the index, so make the card
			nodeIndex += 1
		return True
		
	def makeFront(self, path):
		front = ''
		for node in path[::-1]:
			if node.find('{{start}}') > -1:
				node = node.replace('{{start}}', '')
				front = node + ': ' + front
				break
			else:
				front = node + ': ' + front
				
		if front.endswith(': '):
			front = front[:len(front)-2]

		return front
				
	def makeCardFromPath(self, path):
		
		#print '\ndoing path ', path
		# required to do this here to preserve order of cards
		if not self.checkForForce(path):
			return

		card = RawCard()
		card.back = path.pop()
		
		# remove nodes prior to {{start}}
		card.front = self.makeFront(path)
		
		card.num = 1
		
		subTup = re.subn('{{reverse}}', '', card.back, 1)
		if subTup[1] > 0:
			tmp = card.front
			card.front = subTup[0]
			card.back = tmp
		
		if card.front == self.prevCard.front:
			self.prevCard.num += 1
			self.prevCard.back += constants.htmlBr + card.back
		else:
			self.cards.append(card)
			self.prevCard = card
			
	
	def makeCardsFromPaths(self):
		for i in range(len(self.paths)):
			try:
				self.indexesToIgnore.index(i)
				#print 'ignoring index ', i, self.paths[i]
			except:
				self.makeCardFromPath(self.paths[i])
		
		# adds the '(#)'to the end of cards if needed
		for c in self.cards:
			c.finalizeFront()
				
		
	def readContent(self, path):
		if is_zipfile(path) == False:
			return None
		
		z = None
		try:
			z = ZipFile(path)
			content = z.read('content.xml')
			
		except:
			print 'failed to open zip file or read \'content.xml\''
			z.close()
			return None
		
		self.imageTracker.extractImages(z)
		z.close()

		return content
		
	def setTagNames(self, xml):
		officens = xml.nsmap['office']
		textns = xml.nsmap['text']
		drawns = xml.nsmap['draw']
		xlinkns = xml.nsmap['xlink']
		stylens = xml.nsmap['style']
		fons = xml.nsmap['fo']
		
		names = {}
		names['body'] = '{%s}body' % officens
		names['text'] = '{%s}text' % officens
		names['auto-styles'] = '{%s}automatic-styles' % officens
		names['list'] = '{%s}list' % textns
		names['list-item'] = '{%s}list-item' % textns
		names['p'] = '{%s}p' % textns
		names['s'] = '{%s}s' % textns
		names['line-break'] = '{%s}line-break' % textns
		names['tab'] = '{%s}tab' % textns
		names['span'] = '{%s}span' % textns
		names['frame'] = '{%s}frame' % drawns
		names['image'] = '{%s}image' % drawns
		
		names['href'] = '{%s}href' % xlinkns
		names['name'] = '{%s}name' % stylens
		names['style-name'] = '{%s}style-name' % textns
		names['font-weight'] = '{%s}font-weight' % fons
		names['text-underline-style'] = '{%s}text-underline-style' % stylens
		names['font-style'] = '{%s}font-style' % fons
		names['font-size'] = '{%s}font-size' % fons
		names['background-color'] = '{%s}background-color' % fons
		names['color'] = '{%s}color' % fons
		
		names['style'] = '{%s}style' % stylens
		names['text-properties'] = '{%s}text-properties' % stylens
		names['use-window-font-color']= '{%s}use-window-font-color' %stylens
		self.names = names
		self.builder.names = names
		
	def setStyles(self, xml):
		styles = xml.find(self.names['auto-styles'])
		for style in styles:
			s = Style()
			s.name = style.attrib[self.names['name']]
			
			props = style.find(self.names['text-properties'])
			if props != None:
				if self.names['font-weight'] in props.attrib:
					if props.attrib[self.names['font-weight']] == 'bold':
						s.bold = True
					elif props.attrib[self.names['font-weight']] == 'normal':
						s.resetBold = True						
				
				if self.names['text-underline-style'] in props.attrib:
					if props.attrib[self.names['text-underline-style']] == 'solid':
						s.underline = True
					elif props.attrib[self.names['text-underline-style']] == 'none':
						s.resetUnderline = True
				
				if self.names['font-style'] in props.attrib:
					if props.attrib[self.names['font-style']] == 'italic':
						s.italics = True
					elif props.attrib[self.names['font-style']] == 'normal':
						s.resetItalics = True
						
				if self.names['color'] in props.attrib:
					s.color = props.attrib[self.names['color']]
				elif self.names['use-window-font-color'] in props.attrib:
					if props.attrib[self.names['use-window-font-color']] == 'true':
						s.color = 'default'
				
				if self.names['background-color'] in props.attrib:
					s.bgColor = props.attrib[self.names['background-color']]
				
				if self.names['font-size'] in props.attrib:
					s.size = props.attrib[self.names['font-size']]
			
			#if not s.isDefault():
			self.styles.append(s)
		self.builder.styles = self.styles
			
					
	def getLists(self, parent):
		return self.getTagsByName(parent, self.names['list'])
		
	def getListItems(self, parent):
		return self.getTagsByName(parent, self.names['list-item'])
		
	def getTagsByName(self, parent, tagName):
		children = []
		for child in parent:
			if child.tag == tagName:
				children.append(child)
		return children
		
	def isLeaf(self, element):
		if (len(self.getLists(element)) > 0):
			return False
		else:
			return True
	
	def getText(self, element):
		ps = self.getTagsByName(element, self.names['p'])
		if len(ps) < 1:
			return '{{empty}}'
		else:
			p = ps[0]
			self.builder.parse(p)
			if self.isTextMode:
				return self.builder.plainText
			else:
				return self.builder.formattedText
			
			
	def traverse(self, path, element):
		text = self.getText(element)
		path.append(text)
		node = Node(text)
		
		if not self.isLeaf(element):
			for child in self.getListItems(self.getLists(element)[0]):
				childNode = self.traverse(path[:], child)
				node.children.append(childNode)
		else:
			self.paths.append(path)
		return node
			
	def traverseTree(self, root):
		lists = self.getLists(root)
		if (len(lists) < 1):
			print 'No lists found in this document.'
		
		for l in lists:
			items = self.getListItems(l)
			for e in items:
				self.trees.append(self.traverse([], e))
	
	def makePathsFromFile(self, path):
		content = self.readContent(path)
		if (content == None):
			print 'No content was read.'
			return None
		
		# at this point assumptions are being made about
		# the data
		xml, ns = parse_and_get_ns(StringIO.StringIO(content))
		xml.nsmap = ns
		self.setTagNames(xml)
		
		body = xml.find(self.names['body'])
		text = body.find(self.names['text'])
		
		self.setStyles(xml)
		self.traverseTree(text)		
	
	# returns number of cards created or None if no file is read.
	# do not like the name anymore...
	def makeFromOdt(self, path):
		self.reset()
		
		self.makePathsFromFile(path)
		self.makeCardsFromPaths()
		
		#TODO: somehow consolidate this call and the call in dumpJson
		self.imageTracker.cleanup()
		
		return len(self.cards)

	def dumpJson(self):
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

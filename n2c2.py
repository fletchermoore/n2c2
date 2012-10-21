from zipfile import ZipFile, is_zipfile
from lxml import etree
import re, os

# how much jank?
def rreplace(text, old, new, count):
	return text[::-1].replace(old[::-1], new[::-1], count)[::-1]


class RawCard():
	def __init__(self, front='', back='', num=0):
		self.front = front
		self.back = back
		self.num = num
		
	def asTabDelimited(self):
		tail = ''
		if self.num > 1:
			tail = ' (%d)' % self.num
		u = u"%s%s\t%s\n" % (self.front, tail, self.back)
		return u.encode("utf-8")
		
class TextBuilder():
	def __init__(self, styles = [], names = {}):
		self.styles = styles
		self.names = names
		self.reset()
		
	def reset(self):
		self.frags = []
		self.text = ''
		self.plainText = ''
		self.formattedText = ''
	
	# all text elements in list will be preceeded by a 't' element
	# this is so i can distinguish the fragments
	def add(self, text, isText=False):
		if isText:
			self.frags.append('t')
		self.frags.append(text)
		
	def addSpan(self, prefix, text=None):
		if text:
			self.frags += [prefix, 't', text, '</span>']
		else:
			self.frags.insert(0,prefix)
			self.frags.append('</span>')
			
	
	def parse(self, p):
		self.reset()

		for e in p.iter():
			if e.text != None:
				if e.tag == self.names['span']:
					prefix = self.getSpan(e)
					if prefix:
						self.addSpan(prefix, e.text)
					else:
						self.add(e.text, True)
				else:
					self.add(e.text, True)
			
			if e.tag == self.names['line-break']:
				self.add('<br/>')
			
			# not sure if this is a good idea
			if e.tag == self.names['tab']:
				self.add('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;')
				
			if e.tag == self.names['frame']:
				self.add(self.getImageHtml(e))
			
			if e.tail != None:
				self.add(e.tail, True)
				
		prefix = self.getSpan(p)
		if prefix:
			self.addSpan(prefix)
		
		self.makePlainText()
		self.addCodes()
		self.finalize()
		
	def makePlainText(self):
		positions = self.getTextPositions()
		textFrags = []
		for i in positions:
			textFrags.append(self.frags[i])
		self.plainText = ''.join(textFrags)
	
	def addCodes(self):
		self.replacePrefix('<<', '{{reverse}}')
		self.replacePrefix('||', '{{start}}')
		self.replacePostfix('*', '{{force}}')
		
	def getTextPositions(self):
		positions = []
		for i in range(len(self.frags)-1):
			if self.frags[i] == 't':
				positions.append(i+1)
		return positions
	
	def addLengths(self, positions):
		lengths = []
		for i in positions:
			lengths.append(len(self.frags[i]))
		return zip(positions, lengths)
	
	def removeFirstChars(self, num, positions):
		remainder = num
		for i in positions:
			fragLen = len(self.frags[i])
			if fragLen < remainder:
				self.frags[i] = ''
				remainder -= fragLen
			else:
				self.frags[i] = self.frags[i][remainder:]
				break
				
	def removeLastChars(self, num, positions):
		remainder = num
		for i in positions[::-1]:
			fragLen = len(self.frags[i])
			if fragLen < remainder:
				self.frags[i] = ''
				remainder -= fragLen
			else:
				self.frags[i] = self.frags[i][:len(self.frags[i])-remainder]
				break
		
	def replacePrefix(self, prefix, code):
		if self.plainText.startswith(prefix):
			positions = self.getTextPositions()
			self.removeFirstChars(len(prefix), positions)
			self.add(code)
		
	def replacePostfix(self, postfix, code):
		if self.plainText.endswith(postfix):
			positions = self.getTextPositions()
			self.removeLastChars(len(postfix), positions)
			self.add(code)
	
	# remove 't's and join into one string
	def finalize(self):
		self.formattedText = ''
		for frag in self.frags:
			if frag != 't':
				self.formattedText += frag		
		
		# i fear the images will not always have frames...	
	def getImageHtml(self, frame):
		if frame[0].tag == self.names['image']:
			img = frame[0]
			src = img.attrib[self.names['href']].split('/')[1]
			html = "<img src=\"%s\"/>" % src
			return html
		return ''
		
	def getStyleByName(self, name):
		for s in self.styles:
			if s.name == name:
				return s
		return False
		
	def getSpan(self, element):
		if self.names['style-name'] in element.attrib:
			style = self.getStyleByName(element.attrib[self.names['style-name']])
			if style:
				return "<span style=\"%s\">" % style.asCss()
			
		return None
		
	def getHtmlFormat(self, span, text):
		if self.names['style-name'] in span.attrib:
			style = self.getStyleByName(span.attrib[self.names['style-name']])
			if style:
				return "<span style=\"%s\">%s</span>" % (style.asCss(), text)
			
		return text

class Style():
	def __init__(self):
		self.bold = False
		self.underline = False
		self.italics = False
		
		self.size = None
		self.color = None
		self.bgColor = None
		
		self.name = None
		
	def isDefault(self):
		if (self.bold or self.underline or self.italics
			or self.size or self.color or self.bgColor):
			return False
		return True
		
	def asCss(self):
		text = ''
		if self.bold:
			text += 'font-weight:bold;'
		if self.underline:
			text += 'text-decoration:underline;'
		if self.italics:
			text += 'font-style:italic;'
		if self.size:
			text += 'font-size:%s;' % self.size
		if self.color:
			text += 'color:%s;' % self.color
		if self.bgColor:
			text += 'background-color:%s;' % self.bgColor
		return text

	
class NotesToCards():
	
	def __init__(self):
		self.reset()
		
	def reset(self):
		self.paths = []
		self.indexesToIgnore = []
		self.cards = []
		self.prevCard = RawCard('', '', 1)
		self.styles = []
		self.names = {}
		self.builder = TextBuilder()
		

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
		back = '<br/>'.join(uniqueBacks)
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
			self.prevCard.back += '<br/>' + card.back
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
				
	def getImagePaths(self, zipfile):
		imagePaths = []
		for item in zipfile.namelist():
			if item.startswith('Pictures/'): # will this work on windows?
				imagePaths.append(item)
		return imagePaths
		
	def addImagesToCollection(self, zipfile):
		dest = mw.col.media.dir()
		imagePaths = self.getImagePaths(zipfile)
		for imagePath in imagePaths:
			# Pictures/ 9
			imageName = imagePath[9:]
			imageContent = zipfile.read(imagePath)
			f = open(os.path.join(dest, imageName), 'w')
			f.write(imageContent, )
			f.close()
			#print 'moved image ', imageName
		
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
			
		if self.isAnkiPlugin:
			self.addImagesToCollection(z)
		
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
				
				if self.names['text-underline-style'] in props.attrib:
					if props.attrib[self.names['text-underline-style']] == 'solid':
						s.underline = True
				
				if self.names['font-style'] in props.attrib:
					if props.attrib[self.names['font-style']] == 'italic':
						s.italics = True
						
				if self.names['color'] in props.attrib:
					s.color = props.attrib[self.names['color']]
				
				if self.names['background-color'] in props.attrib:
					s.bgColor = props.attrib[self.names['background-color']]
				
				if self.names['font-size'] in props.attrib:
					s.size = props.attrib[self.names['font-size']]
			
			if not s.isDefault():
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
			return self.builder.formattedText
			
			
	def traverse(self, path, element):
		path.append(self.getText(element))
		
		if not self.isLeaf(element):
			for child in self.getListItems(self.getLists(element)[0]):
				self.traverse(path[:], child) #shallow copy; gross, python
		else:
			self.paths.append(path)
			
	def traverseTree(self, root):
		lists = self.getLists(root)
		if (len(lists) < 1):
			print 'no lists found in this document'
			
		items = self.getListItems(lists[0])
		for e in items:
			self.traverse([], e)
		
	def makeFromOdt(self, path):
		self.reset()
		
		content = self.readContent(path)
		if (content == None):
			print 'No content was read.'
			return
		
		# at this point assumptions are being made about
		# the data
		xml = etree.fromstring(content)
		self.setTagNames(xml)
		
		body = xml.find(self.names['body'])
		text = body.find(self.names['text'])
		
		self.setStyles(xml)
		self.traverseTree(text)
		self.makeCardsFromPaths()
		self.dumpToFile()
		
	def dumpToFile(self):
		path = self.filepath[0:-4] + '-READY_FOR_ANKI.txt'
		f = open(path, 'w')
		for c in self.cards:
			f.write(c.asTabDelimited())
		f.close()
		
	def runAsAnkiPlugin(self):
		self.isAnkiPlugin = True
		action = QAction("Convert Open Document Notes...", mw)
		mw.connect(action, SIGNAL("triggered()"), self.actionConvertNotes)
		mw.form.menuTools.addAction(action)
		
	def actionConvertNotes(self):
		self.filepath = QFileDialog.getOpenFileName(mw, 'Choose File', 
			mw.pm.base, "Open Document Files (*.odt)")
		self.makeFromOdt(self.filepath)
		#self.reportStatus()
		self.reset()
		
	def reportStatus(self):
		if self.status != None:
			tooltip(self.status, 7000)
		
		
app = NotesToCards()
try:
	from aqt import mw
	from aqt.utils import showInfo, tooltip
	from aqt.qt import *
	app.runAsAnkiPlugin()
except ImportError:
	# not anki addon, must be run from command line
	#app.makeFromOdt(path)
	print 'no way to run from command line right now...'

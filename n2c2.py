from zipfile import ZipFile, is_zipfile
from lxml import etree

#temp until command line stuff
path = 'test.odt'


class Card():
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

	
class NotesToCards():
	
	def __init__(self):
		self.reset()
		
	def reset(self):
		self.cards = []
		self.prevCard = Card('', '', 1)
		
	def addCard(self, path):
		card = Card()
		card.back = path.pop()
		card.front = ': '.join(path)
		card.num = 1
		
		if card.back[0:2] == '<<':
			tmp = card.front
			card.front = card.back[2:]
			card.back = tmp
		
		if card.front == self.prevCard.front:
			self.prevCard.num += 1
			self.prevCard.back += '<br/>' + card.back
		else:
			self.cards.append(card)
			self.prevCard = card
		
	def readContent(self, path):
		if is_zipfile(path) == False:
			return None
				
		try:
			z = ZipFile(path)
			content = z.read('content.xml')
			z.close()
		except:
			print 'failed some zip operation'
			return None
		
		return content
		
	def setTagNames(self, xml):
		officens = xml.nsmap['office']
		textns = xml.nsmap['text']
		drawns = xml.nsmap['draw']
		xlinkns = xml.nsmap['xlink']
		
		self.officeBodyTagName = '{%s}body' % officens
		self.officeTextTagName = '{%s}text' % officens
		self.listTagName = '{%s}list' % textns
		self.listItemTagName = '{%s}list-item' % textns
		self.pTagName = '{%s}p' % textns
		self.lineBreakTagName = '{%s}line-break' % textns
		self.tabTagName = '{%s}tab' % textns
		self.spanTagName = '{%s}span' % textns
		self.frameTagName = '{%s}frame' % drawns
		self.imageTagName = '{%s}image' % drawns
		self.hrefAttribName = '{%s}href' % xlinkns
		
	def getLists(self, parent):
		return self.getTagsByName(parent, self.listTagName)
		
	def getListItems(self, parent):
		return self.getTagsByName(parent, self.listItemTagName)
		
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
		
	# i fear the images will not always have frames...	
	def getImageHtml(self, frame):
		if frame[0].tag == self.imageTagName:
			img = frame[0]
			src = img.attrib[self.hrefAttribName].split('/')[1]
			html = "<img src=\"%s\"/>" % src
			return html
		return ''
		
	def getHtmlFormat(self, span):
		return "<span style=\"font-weight:bold\">%s</span>" % span.text
	
	def getText(self, element):
		ps = self.getTagsByName(element, self.pTagName)
		if len(ps) < 1:
			return '{{empty}}'
		else:
			p = ps[0]
			
			text = ''
			for e in p.iter():
						
				if e.text != None:
					if e.tag == self.spanTagName:
						text += self.getHtmlFormat(e)
					else:
						text += e.text
					
				if e.tag == self.lineBreakTagName:
					text += '<br/>'
				
				# not sure if this is a good idea
				if e.tag == self.tabTagName:
					text += '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
					
				if e.tag == self.frameTagName:
					text += self.getImageHtml(e)
				
				if e.tail != None:
					text += e.tail
			
			return text
			
	def traverse(self, path, element):
		path.append(self.getText(element))
		
		if not self.isLeaf(element):
			for child in self.getListItems(self.getLists(element)[0]):
				self.traverse(path[:], child) #shallow copy; gross i hate you python
		else:
			self.addCard(path)
			
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
		
		body = xml.find(self.officeBodyTagName)
		text = body.find(self.officeTextTagName)
		
		self.traverseTree(text)
		
		self.dumpToFile('test.txt')
		
	def dumpToFile(self, path):
		f = open(path, 'w')
		for c in self.cards:
			f.write(c.asTabDelimited())
		f.close()
		
		
app = NotesToCards()
app.makeFromOdt(path)

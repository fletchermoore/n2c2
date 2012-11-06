import constants

class TextBuilder():
	def __init__(self, styles = [], names = {}, path='.'):
		self.styles = styles
		self.names = names
		self.destPath = path
		self.reset()
		
	def reset(self):
		self.frags = []
		self.text = ''
		self.plainText = ''
		self.formattedText = ''
		self.mediaMap = {} # will be key, value: ODT name, new name
	
	# all text elements in list will be preceeded by a 't' element
	# this is so i do not have to re-parse the HTML later for text editing
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
				self.add(constants.htmlBr)
			
			# google docs uses this heavily
			if e.tag == self.names['s']:
				self.add(' ', True)
			
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
		self.strip()
		self.addCodes()
		self.finalize()
	
	# same idea as the python string function, but with fragments
	def strip(self):
		# left side
		startLen = len(self.plainText)
		
		finishLen = len(self.plainText.lstrip())
		diff = startLen - finishLen
		if diff > 0:
			self.removeFirstChars(diff)
		
		# repeat for right side
		finishLen = len(self.plainText.rstrip())
		diff = startLen - finishLen
		if diff > 0:
			self.removeLastChars(diff)
			
		#rebuild plaintext
		self.makePlainText()
		
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
	
	def removeFirstChars(self, num):
		positions = self.getTextPositions()
		remainder = num
		for i in positions:
			fragLen = len(self.frags[i])
			if fragLen < remainder:
				self.frags[i] = ''
				remainder -= fragLen
			else:
				self.frags[i] = self.frags[i][remainder:]
				break
				
	def removeLastChars(self, num):
		positions = self.getTextPositions()
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
			self.removeFirstChars(len(prefix))
			self.add(code)
		
	def replacePostfix(self, postfix, code):
		if self.plainText.endswith(postfix):
			self.removeLastChars(len(postfix))
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
			# apparently it is possible for an empty image tag to exist <draw:image/>
			try:
				# get the href and remove the 'Pictures/' path
				src = img.attrib[self.names['href']].split('/')[1]
				html = "<img src=\"%s\"/>" % self.imageTracker.getName(src)
				return html
			except KeyError:
				return '' # no error handling
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

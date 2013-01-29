import constants
from n2c2lib.debug import debug
from n2c2lib.Style import Style

class TextBuilder():
	def __init__(self, styles = [], names = {}, path='.'):
		self.styles = styles
		self.names = names
		self.destPath = path
		self.isTextMode = False
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
	
	# if inner span does not exist, we still remove the styles from the text
	def addInnerSpan(self, innerSpan, outerSpan, text):
		if innerSpan:
			self.frags += ['</span>', innerSpan, 't', text, '</span>', outerSpan]
		else:
			self.frags += ['</span>', 't', text, outerSpan]
			
			
	def getStyle(self, element):
		if self.names['style-name'] in element.attrib:
			style = self.getStyleByName(element.attrib[self.names['style-name']])
			return style
		return Style() # it is possible for there to be no style given for a paragraph
			
	
	def parse(self, p):
		self.reset()
		paragraphStyle = self.getStyle(p)
		debug("\nParsing paragraph with style: %s" % paragraphStyle.name)
		debug(paragraphStyle.prettyPrint())
		
		for e in p.iter():
			debug("Parsing element with text: %s" % e.text)
			if e.text != None:
				if e.tag == self.names['span']:
					spanStyle = self.getStyle(e)
					debug("Span found: %s" % spanStyle.name)
					debug(spanStyle.prettyPrint())
					style = spanStyle.inherit(paragraphStyle)
					debug("inherited %s" % style.prettyPrint())
					isEqual = style.equals(paragraphStyle)
					debug("paragraph equal span style? %s" % isEqual)
					if isEqual:
						self.add(e.text, True)
					else:
						openSpan = self.getOpenSpan(style)
						# there is no paragraph style, but there is a span style
						if paragraphStyle.isDefault():
							if openSpan:
								self.addSpan(openSpan, e.text)
							else:
								self.add(e.text, True)
						else:
							outerSpan = self.getOpenSpan(paragraphStyle)
							debug("This should be the paragraph span: %s" % outerSpan)
							self.addInnerSpan(openSpan, outerSpan, e.text)
				else:
					self.add(e.text, True)
			
			if e.tag == self.names['line-break']:
				debug('*the line break*')
				self.add(constants.htmlBr)
			
			# google docs uses this heavily
			if e.tag == self.names['s']:
				self.add(' ', True)
			
			# not sure if this is a good idea
			if e.tag == self.names['tab']:
				self.add('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;')
				
			if e.tag == self.names['frame']:
				debug("text mode @ img? %s" % self.isTextMode)
				if self.isTextMode:
					self.add("[img_removed]", True)
				else:
					self.add(self.getImageHtml(e))
			
			if e.tail != None:
				debug("*the tail %s" % e.tail)
				self.add(e.tail, True)
			
			debug(self.frags)
				
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
	
	def getOpenSpan(self, style):
		if style and not style.isDefault():
			return "<span style=\"%s\">" % style.asCss()
		else:
			return None
		
	def getSpan(self, element):
		if self.names['style-name'] in element.attrib:
			style = self.getStyleByName(element.attrib[self.names['style-name']])
			return self.getOpenSpan(style)		
		return None
		
	def getHtmlFormat(self, span, text):
		if self.names['style-name'] in span.attrib:
			style = self.getStyleByName(span.attrib[self.names['style-name']])
			if style:
				return "<span style=\"%s\">%s</span>" % (style.asCss(), text)
			
		return text

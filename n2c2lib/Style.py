from n2c2lib.debug import debug

class Style():
	def __init__(self):
		self.bold = False
		self.resetBold = False
		self.underline = False
		self.resetUnderline = False
		self.italics = False
		self.resetItalics = False
		
		self.size = None
		self.color = None
		self.bgColor = None
		
		self.name = None
	
	def equals(self, style):
		if self.bold != style.bold:
			return False
		if self.italics != style.italics:
			return False
		if self.underline != style.underline:
			return False
		if self.size != style.size:
			return False
		if self.color != style.color:
			return False
		if self.bgColor != style.bgColor:
			return False
		return True
	
	def copy(self):
		style = Style()
		style.bold = self.bold
		style.underline = self.underline
		style.italics = self.italics
		style.size = self.size
		style.color = self.color
		style.bgColor = self.bgColor
		return style
		
	def inherit(self, parent):
		inheritedStyle = self.copy()
		
		if not self.bold:
			inheritedStyle.bold = parent.bold
		if not self.underline:
			inheritedStyle.underline = parent.underline
		if not self.italics:
			inheritedStyle.italics = parent.italics
		if not self.color:
			inheritedStyle.color = parent.color
		if not self.bgColor:
			inheritedStyle.bgColor = parent.bgColor
		if not self.size:
			inheritedStyle.size = parent.size
		
		if self.resetBold:
			inheritedStyle.bold = False
		if self.resetUnderline:
			inheritedStyle.underline = False
		if self.resetItalics:
			inheritedStyle.italics = False
		if self.color == 'default':
			inheritedStyle.color = None
		if self.bgColor == 'transparent':
			inheritedStyle.bgColor = None
		
		return inheritedStyle
		
	def isDefault(self):
		if (self.bold or self.underline or self.italics
			or self.size or self.color or self.bgColor
			or self.resetBold or self.resetUnderline or self.resetItalics):
			return False
		return True
		
	def asCss(self):
		text = ''
		if self.bold:
			text += 'font-weight:bold;'
		elif self.resetBold:
			text += 'font-weight:normal;'
		if self.underline:
			text += 'text-decoration:underline;'
		elif self.resetUnderline:
			text += 'text-decoration:none;'
		if self.italics:
			text += 'font-style:italic;'
		elif self.resetItalics:
			text += 'font-style:normal;'
		if self.size:
			text += 'font-size:%s;' % self.size
		if self.color and self.color != 'default':
			text += 'color:%s;' % self.color
		elif self.color == 'default':
			text += 'color:black;' #ugh
		if self.bgColor:
			text += 'background-color:%s;' % self.bgColor
		return text
	
	def prettyPrint(self):
		css = self.asCss() 
		if css == "":
			css = "None"
		out = "%s css: %s" % (self.name, css)
		return out
	
	def debugStyle(self):
		pass

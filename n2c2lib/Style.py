
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

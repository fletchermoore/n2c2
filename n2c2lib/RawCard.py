

class RawCard():
	def __init__(self, front='', back='', num=0):
		self.front = front
		self.back = back
		self.num = num
	
	# never gets called if running as anki plugin
	# thus numbers are never added to the ends of lists
	# todo: fix
	def asTabDelimited(self):
		tail = ''
		if self.num > 1:
			tail = ' (%d)' % self.num
		u = u"%s%s\t%s\n" % (self.front, tail, self.back)
		return u.encode("utf-8")
	
	def finalizeFront(self):
		if self.num < 2:
			return self.front
		
		tail = ' (%d)' % self.num
		self.num = 1 # neuters multiple calls
		self.front = self.front + tail
		return self.front
		
	



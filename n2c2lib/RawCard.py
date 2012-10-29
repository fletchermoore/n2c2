

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
	



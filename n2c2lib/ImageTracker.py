
# manages a temporary directory for extracted images
# adds images to destination only if unique

import tempfile, shutil, os

class ImageTracker():
	def __init__(self, path='.'):
		self.destPath = path
	
	def importImage(self, extractedName, writeName):
		destFile = os.path.join(self.destPath, writeName)
		srcFile = os.path.join(self.tempDir, extractedName)
		
		shutil.copy(srcFile, destFile)
		
	def createTmpDir(self):
		self.tempDir = tempfile.mkdtemp(prefix='imgs_', dir='.')
	
	
	def cleanup(self):
		self.images = []
		#print 'removing temporary directory', self.tempDir
		shutil.rmtree(self.tempDir)
		
	def extractImages(self, zipfile):
		self.createTmpDir()
		self.images = []
		
		imagePaths = self.getImagePaths(zipfile)
		for imagePath in imagePaths:
			# 'Pictures/' len =9
			imageName = imagePath[9:]
			imageContent = zipfile.read(imagePath)
			f = open(os.path.join(self.tempDir, imageName), 'w')
			f.write(imageContent)
			f.close()
			self.images.append(imageName)
			
	def getImagePaths(self, zipfile):
		imagePaths = []
		for item in zipfile.namelist():
			if item.startswith('Pictures/'): # will this work on windows?
				imagePaths.append(item)
		return imagePaths
	
	def compare(self, newImg, oldImg):
		print 'comparing', self.getPath(newImg), 'to', oldImg
		return True

	# called by TextBuilder whenever an image link is encountered
	# copys that image to destination and then
	# returns the image name that was used
	def getName(self, href):
		writeName = self.makeUniqueFileName(href)
		self.importImage(href, writeName)
		return writeName
	
	# todo: maybe check for existence first
	def getPath(self, imgName):
		return os.path.join(self.tempDir, imgName)
	
	def makeUniqueFileName(self, originalName):
		destFile = os.path.join(self.destPath, originalName)
		if os.path.exists(destFile):
			ext = os.path.splitext(destFile)[1] # if no extension?
			fd, filepath = tempfile.mkstemp(ext, prefix='odt_img_', dir=self.destPath)
			os.close(fd) # just using the name and overwriting later
			filename = os.path.basename(filepath)
			return filename
		else:
			return originalName


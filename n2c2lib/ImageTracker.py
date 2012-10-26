
# manages a temporary directory for extracted images
# adds images to destination only if unique

import tempfile, shutil, os

class ImageTracker():
	def __init__(self, path='.'):
		self.destPath = path
		
	def moveAll(self):
		for img in self.images:
			destFile = os.path.join(self.destPath, img)
			srcFile = os.path.join(self.tempDir, img)
			
			if os.path.exists(destFile):
				print 'file', destFile, 'exists already'
			else:
				shutil.copy(srcFile, destFile)
				print srcFile, 'moved to', destFile
		
		
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
			print 'extracting', imageName
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
            


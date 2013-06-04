from n2c2lib.ImageTracker import ImageTracker
from n2c2lib.TextBuilder import TextBuilder 
from n2c2lib.Style import Style
from n2c2lib.Node import Node
from n2c2lib import ElementTree as etree
from zipfile import ZipFile, is_zipfile
import StringIO

# stolen from someone else on stackoverflow
def parse_and_get_ns(file):
  events = "start", "start-ns"
  root = None
  ns = {}
  for event, elem in etree.iterparse(file, events):
    if event == "start-ns":
      if elem[0] in ns and ns[elem[0]] != elem[1]:
        # NOTE: It is perfectly valid to have the same prefix refer
        #   to different URI namespaces in different parts of the
        #   document. This exception serves as a reminder that this
        #   solution is not robust.  Use at your own peril.
        raise KeyError("Duplicate prefix with different URI found.")
      ns[elem[0]] = "%s" % elem[1]
    elif event == "start":
      if root is None:
        root = elem
  return etree.ElementTree(root), ns



class OdtModel():
    def __init__(self, filePath, mediaPath):
        self.filePath = filePath
        self.imageTracker = ImageTracker()
        self.imageTracker.destPath = mediaPath
        
    
    def getPaths(self, textMode=False):
        self.paths = []
        self.isTextMode = textMode
        content = self.readContent(self.filePath)
        if (content == None):
            print 'No content was read.'
            return []
        
        # at this point assumptions are being made about
        # the data
        xml, ns = parse_and_get_ns(StringIO.StringIO(content))
        xml.nsmap = ns
        self.setTagNames(xml)
        
        body = xml.find(self.names['body'])
        text = body.find(self.names['text'])
        
        self.setStyles(xml)
        self.traverseTree(text)
        
        self.imageTracker.cleanup()
        return self.paths
        
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
        
        self.imageTracker.extractImages(z)
        z.close()

        return content    
    
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
            if self.isTextMode:
                return self.builder.plainText
            else:
                return self.builder.formattedText
            
            
    def traverse(self, path, element):
        text = self.getText(element)
        path.append(text)
        node = Node(text)
        
        if not self.isLeaf(element):
            for child in self.getListItems(self.getLists(element)[0]):
                childNode = self.traverse(path[:], child)
                node.children.append(childNode)
        else:
            self.paths.append(path)
        return node
            
    def traverseTree(self, root):
        self.trees = [] # is this used?
        lists = self.getLists(root)
        if (len(lists) < 1):
            print 'No lists found in this document.'
        
        for l in lists:
            items = self.getListItems(l)
            for e in items:
                self.trees.append(self.traverse([], e))
    
    def setTagNames(self, xml):
        self.builder = TextBuilder()
        self.builder.imageTracker = self.imageTracker

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
        names['s'] = '{%s}s' % textns
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
        names['use-window-font-color']= '{%s}use-window-font-color' %stylens
        self.names = names
        self.builder.names = names
        
    def setStyles(self, xml):
        interprettedStyles = []
        styles = xml.find(self.names['auto-styles'])
        for style in styles:
            s = Style()
            s.name = style.attrib[self.names['name']]
            
            props = style.find(self.names['text-properties'])
            if props != None:
                if self.names['font-weight'] in props.attrib:
                    if props.attrib[self.names['font-weight']] == 'bold':
                        s.bold = True
                    elif props.attrib[self.names['font-weight']] == 'normal':
                        s.resetBold = True                        
                
                if self.names['text-underline-style'] in props.attrib:
                    if props.attrib[self.names['text-underline-style']] == 'solid':
                        s.underline = True
                    elif props.attrib[self.names['text-underline-style']] == 'none':
                        s.resetUnderline = True
                
                if self.names['font-style'] in props.attrib:
                    if props.attrib[self.names['font-style']] == 'italic':
                        s.italics = True
                    elif props.attrib[self.names['font-style']] == 'normal':
                        s.resetItalics = True
                        
                if self.names['color'] in props.attrib:
                    s.color = props.attrib[self.names['color']]
                elif self.names['use-window-font-color'] in props.attrib:
                    if props.attrib[self.names['use-window-font-color']] == 'true':
                        s.color = 'default'
                
                if self.names['background-color'] in props.attrib:
                    s.bgColor = props.attrib[self.names['background-color']]
                
                if self.names['font-size'] in props.attrib:
                    s.size = props.attrib[self.names['font-size']]
            
            #if not s.isDefault():
            interprettedStyles.append(s)
        self.builder.styles = interprettedStyles
            
                    
       
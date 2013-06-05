from n2c2lib.RawCard import RawCard
from n2c2lib.debug import debug
import re, constants

# takes a list of paths (flattened tree from odt) and returns 
# a list of cards (front, back) for
# import into Anki or printing
class CardBuilder():
    
    def __init__(self):
        self.cards = []
        self.indexesToIgnore = []
        self.prevCard = RawCard('', '', 1)
    
    def build(self, paths):
        self.paths = paths
        
        debug("\n\nMaking cards from paths!\n========================")
        self.debugPaths()
        for i in range(len(self.paths)):
            try:
                self.indexesToIgnore.index(i)
                #print 'ignoring index ', i, self.paths[i]
            except:
                self.makeCardFromPath(self.paths[i])
        
        # adds the '(#)'to the end of cards if needed
        for c in self.cards:
            c.finalizeFront()
                
        return self.cards
    
    # returns a subset of self.paths that match the given path
    # up to the final index
    def getMatchingSubset(self, givenPath, finalIndex):
        indexes = []
        for pathIndex in range(len(self.paths)):
            for nodeIndex in range(len(self.paths[pathIndex])):
                if nodeIndex > finalIndex:
                    indexes.append(pathIndex)
                    break
                if self.paths[pathIndex][nodeIndex] != givenPath[nodeIndex]:
                    break
        return indexes
    
    # removes the force tag from the given paths at the given depth    
    def removeForce(self, indexes, depth):
        for i in indexes:
            self.paths[i][depth] = self.paths[i][depth].replace('{{force}}', '')
    
    # called in checkForForce
    def makeCardFromSubset(self, indexes, backIndex):
        debug("makeCardFromSubset()")
        debug(indexes)
        debug("backIndex: %d" % backIndex)
        
        uniqueBacks = []
        for i in indexes:
            maybeBack = self.paths[i][backIndex]
            try:
                uniqueBacks.index(maybeBack)
            except:
                uniqueBacks.append(maybeBack)
        
        num = len(uniqueBacks)
        back = constants.htmlBr.join(uniqueBacks)
        back = re.sub(r'{{.+?}}', '', back)
        #print 'back// ', back
        
        # any of the paths should do, since they should all start the same
        frontPath = self.paths[indexes[0]][:backIndex]
        front = self.makeFront(frontPath)
        if num > 1:
            front += ' (%d)' % num
        #print 'front// ', front
        
        self.cards.append(RawCard(front, back, 1))
        
    def addIgnores(self, indexes, length):
        for i in indexes:
            #print len(self.paths[i]), length
            if (len(self.paths[i]) == length):
                #print 'to be REMOVED ', self.paths[i]
                self.indexesToIgnore.append(i)
        
    # return true to continue making the card after dealing with the
    # forced list
    def checkForForce(self, path):
        nodeIndex = 0
        for node in path:
            if node.find('{{force}}') > -1:
                debug("Force found in %d of path:" % nodeIndex)
                debug(path)
                matchingIndexes = self.getMatchingSubset(path, nodeIndex)
                # if the '*' is used inappropriately, it is possible for matchingIndexes
                # to return an empty list. check for it
                if len(matchingIndexes) > 0:
                    self.removeForce(matchingIndexes, nodeIndex)
                    self.makeCardFromSubset(matchingIndexes, nodeIndex+1)
                    self.addIgnores(matchingIndexes, nodeIndex+2)
                    # check to see if the current card was added to the ignore list
                    # if it was, do not continue with card creation
                    currentIndex = self.paths.index(path) # this should never fail
                    try:
                        self.indexesToIgnore.index(currentIndex)
                        return False # do not continue
                    except:
                        return True # not ignoring the index, so make the card
            nodeIndex += 1
        return True
    
    def makeCardFromPath(self, path):
        # make sure there are enough nodes in path to make a card
        if len(path) < 2:
            return
                
        # required to do this here to preserve order of cards
        if not self.checkForForce(path):
            return

        card = RawCard()
        card.back = path.pop()
                
        card.front = self.makeFront(path)
        
        card.num = 1
        
        subTup = re.subn('{{reverse}}', '', card.back, 1)
        if subTup[1] > 0:
            tmp = card.front
            card.front = subTup[0]
            card.back = tmp
        
        if card.front == self.prevCard.front:
            self.prevCard.num += 1
            self.prevCard.back += constants.htmlBr + card.back
        else:
            self.cards.append(card)
            self.prevCard = card


    def makeFront(self, path):
        nodes = []
        delimiter = ': '
        front = ''
        
        # build the new list in reverse order to presentation
        for node in path[::-1]: # moves through paths in reverse order
            if node.find('{{nodelimiter}}') > -1:
                node = node.replace('{{nodelimiter}}', '')
                nodes.append(' ') # no delimiter isn't literally true :)
                nodes.append(node)
            elif node.find('{{swap}}') > -1: # for the moment, just remove the tag
                node = node.replace('{{swap}}', '')
                nodes.append(delimiter)
                nodes.append(node)
            elif node.find('{{start}}') > -1:
                node = node.replace('{{start}}', '')
                nodes.append(delimiter)
                nodes.append(node)
                break
            else:
                nodes.append(delimiter)
                nodes.append(node)
                
        nodes.reverse()
        nodes.pop()
        return ''.join(nodes)

    # prettier printing of paths
    def debugPaths(self):
        index = 0
        for path in self.paths:
            debug(index)
            debug(path)
            index += 1
    
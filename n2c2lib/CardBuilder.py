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
        
        # switch the front and back of the card
        subTup = re.subn('{{reverse}}', '', card.back, 1)
        if subTup[1] > 0:
            tmp = card.front
            card.front = subTup[0]
            card.back = tmp
        
        if card.front == self.prevCard.front:
            if card.back != '' and card.back[0:5] != '<img ':
                self.prevCard.num += 1
            self.prevCard.back += constants.htmlBr + card.back
        else:
            self.cards.append(card)
            self.prevCard = card

    # if you have a list [a, b><, c, d]
    # create the list [c, d, a, b]
    # What good is this? Suppose you want to make a bunch of
    # cards with the same prompt. Without this function, you have to
    # type the prompt over and over. With swap you can just put it at
    # the top of your list
    # I cannot really come up with use cases for more than one swap
    # but now it can be done. 
    # maybe it would be more intuitive in reverse?
    def doSwaps(self, path):
        for i in range(0, len(path)):
            if path[i].find('{{swap}}') > -1:
                path[i] = path[i].replace('{{swap}}', '')
                firstPart = path[0:i+1]
                secondPart = path[i+1:]
                secondPart.extend(firstPart)
                return self.doSwaps(secondPart)
        return path

    def makeFront(self, path):
        path = self.doSwaps(path)
        
        nodes = []
        delimiter = ': '
        front = ''
            
        # build the new list in reverse order to presentation
        for node in path[::-1]: # moves through paths in reverse order
            if node.find('{{nodelimiter}}') > -1:
                node = node.replace('{{nodelimiter}}', '')
                nodes.append(' ') # no delimiter isn't literally true :)
                nodes.append(node)
            elif node.find('{{start}}') > -1: #reached start point -> terminate
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
    
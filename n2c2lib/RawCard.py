
try:
	from aqt import mw
	from anki import notes
except ImportError:
	pass
	
	
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
		
	def isDuplicate(self):
		q = '\'note:Basic\' \'Front:%s\'' % self.front
		ids = mw.col.findCards(q)
		print self.front, ids
		return False

        # by Tiago
        #  The main change here was adding a new function, import_card,
        # that allows us to import cards directly to anki without the
        # need to generate any extra files
	def import_card(self):
#		self.isDuplicate()
            #  We will import a RawCard as a note with type 'Basic',
            # which only has a front field and a back field
            
            #  First we get the 'Basic' model for cards.
            #  mw.col is the colection associated with the current main window,
            # that is, it's the collection belonging to the user.
            #  mw.col.models is the model manager of the collection.
            #  byName is a method that returns a model with a certain name,
            # or None if it doesn't exist.
		basic_model = mw.col.models.byName("Basic")
            #  In Anki 2.0, we select the deck of the card in the model field,
            # (I don't understand why, but whatever).  We want to add the
            # card to the current deck.
		basic_model['did'] = mw.col.conf['curDeck']
            #  The previous line is weird; we are saying that the
            # deck id (did) of the basic model is the id of the current deck
            # ('curDeck') stored in the configuration field of the collection
            # mw.col.conf.
            
            # Then we create a new note with that model.
            # To create a Note, we must supply two arguments:
            #  - a collection to which we will add the note (mw.col)
            #  - a model for the note (basic_model)
		new_note = notes.Note(mw.col, basic_model)
            # The fields of a card are an ordered list of strings.
            # Setting the front and back fields of the note is trivial
		new_note.fields = [self.front, self.back]
            # If you want to extend the code to add tags, you can use a
            # variation of the following code, where tags is the list of
            # strings, each string being a tag:
            ######################################################## 
            ## for tag in tags:
            ##     new_note.addTag(tag)
            ########################################################
            # Now the note is created, and you only have to add it to
            # the collection:
		mw.col.addNote(new_note)

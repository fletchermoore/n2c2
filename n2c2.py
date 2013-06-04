# Author: Fletcher Moore
# contributors: Tiago Barroso
# this software is public domain.
from n2c2lib.NotesToCards import NotesToCards
import n2c2lib.debug
import sys
		
	
	
class AnkiN2C2Plugin():
	def __init__(self):
		self.core = NotesToCards()
		self.reset()
		
	def reset(self):
		self.numCreated = 0 # number created from the odt, even if not added to deck
		self.duplicates = []
		self.added = []
	
	# too verbose?
	def alertUser(self):
		text ='%d new card(s) added. %d card(s) were duplicates' % (
																	len(self.added),
																	len(self.duplicates))
		text += '\n\nNEW CARDS:\n==========\n'
		for card in self.added:
			text += stripHTML(card.front) + '\n'
		
		text += '\nDUPLICATES:\n===========\n'
		for card in self.duplicates:
			text += stripHTML(card.front) + '\n'
			
		showText(text)
		
	def setup(self):
		action = QAction("Import ODT...", mw)
		mw.connect(action, SIGNAL("triggered()"), self.actionImportFromOdt)
		mw.form.menuTools.addAction(action)
        
	def actionImportFromOdt(self): # is the filepath used again in core?
		self.core.filepath = QFileDialog.getOpenFileName(mw, 'Choose File', 
		        mw.pm.base, "Open Document Files (*.odt)")
		self.numCreated = self.core.makeFromOdt(self.core.filepath,
											mw.col.media.dir())
		cards = self.core.cards
		self.import_to_anki(cards)
		self.core.reset()
		#  We must update the GUI so that the user knows that cards have
		# been added.  When the GUI is updated, the number of new cards
		# changes, and it provides the feedback we want.
		# If we want more feedback, we can add a tooltip that tells the
		# user how many cards have been added.
		# The way to update the GUI will depend on the state
		# of the main window. There are four states (from what I understand):
		#  - "review"
		#  - "overview"
		#  - "deckBrowser"
		#  - "resetRequired" (we will treat this one like "deckBrowser)
		if mw.state == "review":
		    mw.reviewer.show()
		elif mw.state == "overview":
		    mw.overview.refresh()
		else:
		    mw.deckBrowser.refresh() # this shows the browser even if the
		      # main window is in state "resetRequired", which in my
		      # opinion is a good thing
		self.alertUser()
		self.reset()
				
	def import_to_anki(self, cards):
		for c in cards:
			self.import_card(c)
	
	# if the card has an image in it, it will always be unique
	# because a new image is created ea time
	# todo: fix
	def isDuplicate(self, card):
		#query the db directly since Anki's search will not match ':' and '(', eg

		fields = joinFields([card.front, card.back])
		q = 'select id from notes where flds = ?'
		noteIds = mw.col.db.list(q, fields)
		
		if len(noteIds) == 0:
			# no notes match, we are done
			return False
		else:
			# notes match, but are they in the current deck?
			deckId = mw.col.conf['curDeck']
			q = 'select id from cards where nid = ? and did = ?'
			for noteId in noteIds:
				cardIds = mw.col.db.list(q, noteId, deckId)
				if len(cardIds) > 0:
					return True
			return False # matches were found, but not in the current deck
		
	def handleDuplicate(self, card):
		self.duplicates.append(card)

			
        # by Tiago
        #  The main change here was adding a new function, import_card,
        # that allows us to import cards directly to anki without the
        # need to generate any extra files
	def import_card(self, card):
		if self.isDuplicate(card):
			self.handleDuplicate(card)
		else:
		
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
			new_note.fields = [card.front, card.back]
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
			self.added.append(card)

try:
	# if Anki is found, we are an Anki addon
	from anki.utils import joinFields, stripHTML
	from aqt.utils import showText
	from anki import notes
	from aqt import mw
	from aqt.utils import showInfo, tooltip
	from aqt.qt import *	
	plugin = AnkiN2C2Plugin()
	plugin.setup()
	
except ImportError as err:
	# not anki addon, run from command line
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument("file", help="An odt file to convert to flashcards")
	parser.add_argument('-o', '--out', help="Filename to write to")
	parser.add_argument('-d', '--debug', help="Dump debug output to stdout", action="store_true")
	parser.add_argument('-j', '--json', help="Display contents as json in stdout", action="store_true")
	parser.add_argument('-t', '--text', help="Ignore formatting", action="store_true")
	args = parser.parse_args()
	
	if args.debug:
		print "Debug on"
	n2c2lib.debug.isDebug = args.debug

	app = NotesToCards()
	app.configure(args)
	app.execute()
	

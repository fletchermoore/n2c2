This project is no longer maintained. It does not work with Anki2.1.


Installing
==========
1. Get Anki at http://ankisrs.net
2. Add the `n2c2.py` file and the `n2c2lib` folder with its contents to the `Anki/addons` folder

That's it.

Use
===
1. create your open document format text file. (ie, .odt)
2. launch Anki
3. within Anki, select `Tools -> Import ODT...` and then choose your file. _This action 
immediately creates new cards within your current open deck without confirmation_

Tutorial
========

Basics
------

Flash cards will be constructed only from the lists found in the document. All other text is ignored,
so you can write whatever you want. The most nested leaves become the backs of your cards. 
The front is the path down to the leaf separated by colons (`:`).

Example:

<ul>
<li> hypertension
 <ul><li> blood pressure over 140</li>
     <li> types
       <ul>
          <li>essential</li>
          <li>secondary</li>
          <li>malignant</li>
       </ul>
     </li>
 </ul>
</li>
</ul>

will make 2 cards:

> front: `hypertension `
> back: `blood pressure over 140`
> 
> front: `hypertension: types (3) `
> back: `essential<br/>secondary<br/>malignant`

(the `<br/>` tag will render in Anki as a line break)

Special Characters: "Force" * (the Asterisk)
--------------------------------------------

Notice that in the above example, the types sublist was collapsed into one card. 
What would happen if the list looked like this instead?

<ul>
<li> hypertension
 <ul><li> blood pressure over 140</li>
     <li> types
       <ul>
          <li>essential
          </li>
          <li>secondary
            <ul>
              <li>hypertension caused by some other underlying condition</li>
            </ul>
         </li>
          <li>malignant</li>
       </ul>
     </li>
 </ul>
</li>
</ul>

You would end up with some hideous result like so:

> front: `hypertension `
> back: `blood pressure over 140`
> 
> front: `hypertension: types`
> back: `essential`
> 
> front: `hypertension: types: secondary`
> back: `hypertension caused by some other underlying condition`
> 
> front: `hypertension: types`
> back: `maligant`

No doubt, this is not what you want. Normally the program checks to see if connsecutive terminal leaves have
the same front. If they do, it collapses them into one card. In this case the leaves have been split apart by a
quite different card. To get around this, add the `*` to the end of the `types` bullet.
This symbol forces the program to make a card at this point, using only the immediate subitems. Here it will
produce a list of all the subitems.

<ul>
<li> hypertension
 <ul><li> blood pressure over 140</li>
     <li> types*
       <ul>
          <li>essential
          </li>
          <li>secondary
            <ul>
              <li>hypertension caused by some other underlying condition</li>
            </ul>
         </li>
          <li>malignant</li>
       </ul>
     </li>
 </ul>
</li>
</ul>

Much better:

> front: `hypertension `
> back: `blood pressure over 140`
> 
> front: `hypertension: types (3) `
> back: `essential<br/>secondary<br/>malignant`
> 
> front: `hypertension: types: secondary`
> back: `hypertension caused by some other underlying condition`


Special Characters: "Start" ||
------------------------------

Now, you might find the fronts of your cards getting obnoxious. Above, `hypertension: types: secondary` might 
not sit well with you. But you wouldn't want to move that information to the top level in your notes. It is
after all a subset of hypertension. Instead use the double pipe characters `||`, which basically trim the
front of the card such that it starts at the pipes. *These must be the first two characters in the bullet list!*

<ul>
<li> hypertension
 <ul><li> blood pressure over 140</li>
     <li> types*
       <ul>
          <li>essential
          </li>
          <li>||secondary hypertension
            <ul>
              <li>hypertension caused by some other underlying condition</li>
            </ul>
         </li>
          <li>malignant</li>
       </ul>
     </li>
 </ul>
</li>
</ul>

Results:

> front: `hypertension `
> back: `blood pressure over 140`
> 
> front: `hypertension: types (3) `
> back: `essential<br/>secondary hypertension<br/>malignant`
> 
> front: `secondary hypertension`
> back: `hypertension caused by some other underlying condition`

Notice I changed the text from `secondary` to `secondary hypertension`. 
`secondary` would not make much sense as the prompt.

Special Characters: "Reverse" <<
--------------------------------

Like the pipes `||`, put the double angle brackets `<<` at the start of the line. This code tells the program to flip the
front and back of the card. Here is an example. Notice I am using the "start" code again as well to eliminate 
excess verbosity.

<ul>
<li> hypertension
 <ul><li> blood pressure over 140</li>
     <li> types*
       <ul>
          <li>||essential hypertension
            <ul>
              <li>&lt;&lt;the most common form of hypertension</li>
            </ul>
          </li>
          <li>||secondary hypertension
            <ul>
              <li>hypertension caused by some other underlying condition</li>
            </ul>
         </li>
          <li>malignant</li>
       </ul>
     </li>
 </ul>
</li>
</ul>

Results

> front: `hypertension `
> back: `blood pressure over 140`
> 
> front: `hypertension: types (3) `
> back: `essential hypertension<br/>secondary hypertension<br/>malignant`
> 
> front: `the most common form of hypertension`
> back: `essential hypertension`
> 
> front: `secondary hypertension`
> back: `hypertension caused by some other underlying condition`

A word of caution: some word processors will replace the double angle brackets with a single character 
(the left guillemet [aka French quotation marks]) If this 
happens the "reverse" code will not be interpreted. Also, if you have subitems under a reversed card, the card will
not reverse correctly. The reversed bullet must be a terminal leaf.

Advanced Use Cases
------------------

You can find additional formatting tricks in the Wiki on Github.


Text Formatting and Images
--------------------------

The program will convert bold, underline, italics, front color, and background color (highlight) into the
appropriate CSS and HTML codes. Anki will render these. Any other formatting will be ignored when the flash
cards are created, but don't let that stop you from using it to decorate your notes!

Images included in the `.odt` are added to your `collection.media` folder. The image must actually be
anchored within the list itself or it will be ignored. This anchoring is not the default in Libre Office. You
can change an image's anchoring state by right clicking it.


Troubleshooting/Parting Words
=============================

I have been using it for a while with LibreOffice and it works well. Currently there is a rareish bug wherein the
formatting will become screwed up. I have not gotten around to fixing it yet. I have not tested this in gdoc created
documents lately, but it should work.

In LibreOffice, if you delete a bullet, but leave the text, this will cause the text to be ignored. I have not bothered
to figure out why this is the case, but to avoid this problem use `<shift>+<enter>` to create linebreaks instead of
deleting bullets.

Importing the same file again will duplicate all of the cards and images. Checking for prior 
existence is on my todo list.
For now you will need to manage that aspect yourself.

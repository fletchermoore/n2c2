Installing
==========
1. Get Anki at ankisrs.net
2. Add the n2c2.py file to the Anki/addons folder

That's it.

Use
===
1. create your open document format text file. (ie, .odt)
2. launch Anki
3. within Anki, select Tools -> Convert Open Document Notes... and then choose your file.
4. within Anki, select File -> Import... and then choose the newly created -READY_FOR_ANKI.txt file
5. select the deck and then click Import

ODT format
==========
Flash cards will be constructed from the first list found in the document. All other text is ignored,
so you can write whatever you want.

Basics
------

The most nested leaves become the backs of your cards. The front is the path down to the leaf.
Example:

<ul>
<li> hypertension</li>
<li><ul><li> blood pressure over 140</li></ul></li>
<li> types</li>
<li><ul>
<li> essential</li>
<li> secondary</li>
<li> malignant</li>
</ul></li>
</ul>

will make 2 cards:

front: hypertension 
back: blood pressure over 140

front: hypertension: types (3) 
back: essential, secondary, malignant (except with linebreaks instead of commas)
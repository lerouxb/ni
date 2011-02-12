NI
==

Ni is a text editor slash text editor framework.


INSTALLATION
============

pygments: <http://pygments.org/>  
Ubuntu package: python-pygments

chardet: <http://chardet.feedparser.org/>   
Ubuntu package: python-chardet

The urwid version requires urwid. <http://excess.org/urwid/>  
Ubuntu package: python-urwid.

The GTK version requires pygtk2: <http://www.pygtk.org/>  
Ubuntu package: python-gtk2


GOALS
=====


Try out and implement new/modern user interface ideas
-----------------------------------------------------

* Document tree (open documents only), NOT tabs.

* Smart workspaces.

* Quick-open that integrates with workspaces.

* Search that's even better than JEdit's hyper-search. The results should update automatically as you type so that it is always in sync. It should also integrate with workspaces, use modern regular expressions and globs and make it easy to search across multiple files: open documents, a directory and sub-directories or an entire workspace. You should also be allowed to have multiple live searches running at the same time.

* Modern gui app keybindings, style and feel.


Try creating an editor framework for easily building your own editor
--------------------------------------------------------------------

Some clear interfaces to make it easy to re-use most code, actions, etc. You should just have to glue together the custom gui elements. Obviously good separation of display and other code. It should be very easy to port to different gui toolkits by simply implementing a different editor. It should also be easy to make up your own key bindings or editing "paradigms" while reusing 90% of the code. 


NOT an IDE
----------

Just a good programming text editor. Emphasis on "projects" (as in large groups of files)


IMPLEMENTED
===========

All the usual movement and selection commands, Undo/Redo of all editor actions. Rather hackish syntax hilighting via pygments. Urwid and GTK variants of the editor. A sparse document tree, workspaces, quick open.


NOT IMPLEMENTED
===============

Started on search, but stopped having the time to work on it before I got very far. I recently moved to OSX, so I'll have to implement an OSX editor on top of all of this...


NEWER IDEAS
===========


Parsing
-------

Sometimes you want to treat code as text and sometimes you want to treat it as some kind of AST. Pygments just spits out a flat token stream which is fine for syntax hilighting, but I'm already starting to have trouble just to try and optimise the tokenizing to not unnecessarily parse the entire document all the time. Obviously you have to backtrack a bit, but it is tricky finding a "safe" spot as we don't have the full state at any point.. I can't really blame pygments because it was meant for hilighting snippets of code as html and it was probably never intended for use in a text editor.

What's really needed is one parser system that creates fast parsers that can be paused and resumed and that allows you to change and only reparse parts of it, etc. The types of things you would want to do in an editor. And at the same time it would be nice if you end up with a real, accurate AST.

Basically someone has to finish Gazelle: http://www.reverberate.org/gazelle/ It would actually make sense to write it once in C and then just have bindings to every language out there. Multiple different editors and all sorts of other projects could then use the same parsers.

That sort of thing would make all sorts of new and interesting things possible in a text editor. A lot of these things already do get done in vim and emacs, butthere's a crazy amount of duplicated effort and these per-editor parsers often have bugs, things get out of sync, etc.


Workspaces
----------

I think the workspaces thing is too complicated. It should just auto-detect git repositories, read in .gitignore and generally just work without any configuration.


Multiple windows/views/splits
-----------------------------

The Document and View interfaces might need some work so that you can have the same file open at two places at the same time. The document tree widget thing will also require changes so that it would know where to open it, which window to switch to, etc.


# itemRadar
QGraphicsItem based GIU for tracking data / tasks based on a visual priority

# Why

Primarily this was written as a way for me to use MongoDb and to also use QGraphicsItem.
I'm a technical artist in the games sector working in Maya.  The QGraphics api would
be useful for a node editor or as a character control picker.  This work is for fun and
curiosity.   I think this is also fun and graphical way to track interesting tech
projects and rnd from around the web.  It could be a lightweight asset tracking system
built directly into Maya.

I would also like to take this further with a web implementation using https://www.meteor.com/

# Features

* Many radar graphs can be open at once.
* Data is stored in mongoDb and can be exported per graph to a json file
* Items distance to the centre can denote priority
* Items exist in a `zone` that can be filtered.  Zone are labeled P1, P2 etc
* Items can be tagged and filtered by tag
* Items can be colored for further quick visual labeling
* Items carry a description and comments history

# Known Issues

* Filters are not yet applied to the radar graphics scene.  Just the attribute editor.
* Items are simple graphic dots.  Show label feature needs to be developed.
* Would be good to be able to `Zoom` into the canvas for more clarity
* Links to web pages in the links field should change the dot to show the user they can jump to the web page
* Items should be locked when selected in the database
* The model needs to update the locked item status per tick to show multiple users working on the same board
* Items need role outs child widgets.

# Requirements

* local mongoDb installation
* Python 2.7

# TODO

* setup.py


# Screen Grabs

![Alt text](docs/screengrab_01.png?raw=true "Title")




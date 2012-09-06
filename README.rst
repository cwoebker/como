coco: batteries complete
========================

`coco.py <http://cwoebker.github.com/coco>`_ is a minimalistic utillity to monitor and log battery health & more.

`Status <http://travis-ci.org/cwoebker/coco>`_
----------------------------------------------

.. image:: https://secure.travis-ci.org/cwoebker/coco.png?branch=master

Usage
-----

``coco``
    Saves the current battery state.

``coco stats``
    Prints information about battery and battery history.

``coco reset``
    Removes all entries in database.

``coco --help``
    Shows a complete help.

``coco --version``
    Shows the current version.


Installation
------------

Installing coco is simple:

    $ pip install coco


Advanced
--------

``coco.py`` stores all battery information in the file ``~/.coco``.
You are free to do whatever you want with the data in that file, 
its yours after all.

So go out there and hack some code!

Question's and suggestions, feel free to shoot me an email <me@cwoebker.com>

Follow `@cwoebker <http://twitter.com/cwoebker>`_


Contribute
----------

Fork and contribute!

TODO
----

    - Cross-Platform

---------------

Copyright (c) 2012, Cecil Woebker.
License: BSD (see LICENSE for details)

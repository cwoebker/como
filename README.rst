coco: batteries complete
========================

`coco.py <http://cwoebker.github.com/coco>`_ is a minimalistic utillity to monitor and log battery health & more. (Mac only)

`Status <http://travis-ci.org/cwoebker/coco>`_
----------------------------------------------------

.. image:: https://secure.travis-ci.org/cwoebker/coco.png?branch=master

Usage
-----

``relo config``
    Changes settings and other global variables.

``relo update``
    Updates the relo installation.

``relo index``
    Creates an index of a given directory.

``relo search``
    Either searches a filesystem or an index if available.

``relo stats``
    Analyzes a filesystem or an index if available.


Installation
------------

Installing coco is simple:

    $ pip install legit


Advanced
--------

``coco.py`` stores all battery information in the file ``~/.coco``. You are free to do whatever you want with the data in that file, its yours after all. 

So go out there and hack some code!

Question's and suggestions, feel free to shoot me an email <me@cwoebker.com>

Follow `@cwoebker <http://twitter.com/cwoebker>`_


Caveats
-------

- **Warning:** This is still beta. Do not use for anything hugely important.
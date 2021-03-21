Pixsaw
======

Cuts an image up into multiple pieces by following pixel lines that contrast
with targetted piece color.  Inspired by scissors, but more flexible with the
drawback of possibly losing some pixels in the process.

Installing
----------

Requires:

* `Pillow <http://github.com/python-imaging/Pillow>`_

Install with pip in editable mode for developing and use virtualenv to isolate
python dependencies::

    $ python3 -m venv .
    $ source ./bin/activate
    $ pip install -e .


Usage
-----

Running the ``pixsaw.py`` script will show some help.  It basically needs a
path to a directory to store the generated files, an image that shows where to
cut, and the image that should be cut into pieces.

Example::

    $ mkdir tmp-small-puzzle-example
    $ pixsaw --dir tmp-small-puzzle-example --lines examples/small-puzzle-lines.png examples/320px-White_Spoon_Osteospermum.jpg



The puzzle lines:

.. image:: https://github.com/jkenlooper/pixsaw/raw/master/examples/small-puzzle-lines.png


The image:

.. image:: https://github.com/jkenlooper/pixsaw/raw/master/examples/320px-White_Spoon_Osteospermum.jpg


Image from: http://en.wikipedia.org/wiki/File:White_Spoon_Osteospermum.JPG

The output (combined into one file with glue to better show it):

.. image:: https://github.com/jkenlooper/pixsaw/raw/master/examples/pieces-combined-with-glue.png



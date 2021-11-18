#!/usr/bin/env python

import logging
from optparse import OptionParser

from pixsaw.base import Handler

from pixsaw._version import __version__


def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = OptionParser(
        usage="%prog --dir path/to/dir --lines lines.png [options] path/to/image",
        version=__version__,
        description="Cut a picture into pieces by cutting along pixel lines",
    )

    parser.add_option(
        "--dir",
        "-d",
        action="store",
        type="string",
        help="Set the directory to store the clip files in.",
    )
    parser.add_option(
        "--lines",
        "-l",
        action="store",
        type="string",
        help="Set the lines file.",
    )
    parser.add_option(
        "--gap",
        default=True,
        action="store_false",
        help="Leave gap between pieces.",
    )

    (options, args) = parser.parse_args()

    if not args and not (options.dir and options.lines):
        parser.error("Must set a directory and lines file with an image")

    handler = Handler(options.dir, options.lines, include_border_pixels=options.gap)
    for image in args:
        handler.process(image)


if __name__ == "__main__":
    main()

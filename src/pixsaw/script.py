#!/usr/bin/env python

import logging
from optparse import OptionParser

from setuptools_scm import get_version

from pixsaw.base import Handler

def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = OptionParser(
            usage="%prog --dir path/to/dir --lines lines.png [options] path/to/image",
            version=get_version(),
            description="Cut a picture into pieces by cutting along pixel lines")

    parser.add_option("--dir", "-d",
            action="store",
            type="string",
            help="Set the directory to store the clip files in.",)
    parser.add_option("--lines", "-l",
            action="store",
            type="string",
            help="Set the lines file.",)

    (options, args) = parser.parse_args()

    if not args and not (options.dir and options.lines):
        parser.error("Must set a directory and lines file with an image")

    handler = Handler(options.dir, options.lines)
    for image in args:
        handler.process(image)

if __name__ == '__main__':
    main()

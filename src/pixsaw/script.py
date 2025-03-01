#!/usr/bin/env python

import sys
import logging
import argparse

from pixsaw.base import Handler, HandlerError
from pixsaw._version import __version__


def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(
        description="Cut a picture into pieces by cutting along pixel lines",
    )
    parser.add_argument('--version', action='version', version=__version__)

    parser.add_argument(
        "--dir",
        "-d",
        action="store",
        help="Set the directory to store the clip files in.",
    )
    parser.add_argument(
        "--lines",
        "-l",
        action="store",
        help="Set the lines file.",
    )
    parser.add_argument(
        "--gap",
        default=True,
        action="store_false",
        help="Leave gap between pieces.",
    )
    parser.add_argument(
        "--floodfill-min",
        action="store",
        default=400,
        type=int,
        help="Minimum pixels to floodfill for a piece",
    )
    parser.add_argument(
        "--floodfill-max",
        action="store",
        default=50_000_000,
        type=int,
        help="Max pixels to floodfill at a time",
    )
    parser.add_argument(
        "--rotate",
        action="store",
        default="0,0,1",
        help="Random rotate pieces range for start, stop, step",
    )

    parser.add_argument("image", nargs="+", help="JPG image")

    args = parser.parse_args()
    images = args.image

    if not images and not (args.dir and args.lines):
        parser.error("Must set a directory and lines file with an image")

    rotate = tuple(range(*(int(x) for x in args.rotate.split(","))))

    handler = Handler(args.dir, args.lines, include_border_pixels=args.gap, floodfill_min=args.floodfill_min, floodfill_max=args.floodfill_max, rotate=rotate)
    try:
        handler.process(images)
    except HandlerError as err:
        sys.exit(err)


if __name__ == "__main__":
    main()

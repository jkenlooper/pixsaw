import logging
from optparse import OptionParser

from PIL import Image


def floodfill(pixels, bbox, targetcolor=(255,255,255,255), edgecolor=(0,0,0,255)):
    "Flood Fill using a stack"
    left, top, right, bottom = bbox

    thestack = set()
    thestack.add( (left, top) )
    clip = set()

    while len(thestack) != 0:
        x, y = thestack.pop()

        if (x,y) in clip:
            continue

        if x > right or x < left or y > bottom or y < top:
            continue

        p = pixels[(x,y)]
        if p != targetcolor:
            if p[3] > 0: # if not completly transparent
                # include border pixels
                clip.add( (x,y) )

            continue

        clip.add( (x,y) )

        thestack.add( (x + 1, y) ) # right
        thestack.add( (x - 1, y) ) # left
        thestack.add( (x, y + 1) ) # down
        thestack.add( (x, y - 1) ) # up

    # save image
    clipimg = Image.new("RGBA",
            (bbox[2] - bbox[0], bbox[3] - bbox[1]),
            (0,0,0,0))


    logging.debug("clipimg size %s", (clipimg.size))
    logging.debug("clipimg length %s", (clipimg.size[0] * clipimg.size[1]))
    pixel_seq = []
    for row in xrange(top, bottom):
        for col in xrange(left, right):
            if (col, row) in clip:
                #TODO: this should be changed to get pixel from the target image
                pixel_seq.append( pixels[(col,row)] )
            else:
                # add a transparent pixel
                pixel_seq.append( (0,0,0,0) )

    logging.debug("pixel_seq length %s", len( pixel_seq ))

    clipimg.putdata( pixel_seq )
    clipimg.save('clip-circle.png')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    im = Image.open('white-circles.png')

    pixels = im.load()

    bbox = im.getbbox()
    width, height = im.size

    floodfill(pixels, bbox)



def main():
    parser = OptionParser(
            usage="%prog --dir path/to/dir --lines lines.png [options] path/to/image",
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

    mydir = options.dir

    clips = Clips(svgfile=options.svg,
                clips_dir=mydir,
                size=(options.width, options.height))

    #TODO: could probably use the scissors on multiple images
    scissors = Scissors(clips, args[0], mydir)
    scissors.cut()


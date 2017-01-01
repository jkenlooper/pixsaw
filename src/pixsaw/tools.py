def floodfill(pixels, bbox, origin=None, targetcolor=(255,255,255,255),
        tolerance=0):
    """Flood Fill at origin using a stack.
    Returns a set of pixels that were filled.

    :param pixels: sequence of pixels for a lines_image
    :param bbox: Bounding box to stay within
    :param origin: Point to floodfill at. Defaults to left, top of bbox.
    :param targetcolor: The Target color pixel with alpha.
    :param tolerance: Fuzziness when filling in.
    """
    left, top, right, bottom = bbox
    if origin == None:
        origin = (left, top)

    thestack = set()
    thestack.add( origin )
    clip = set()

    while len(thestack) != 0:
        x, y = thestack.pop()

        if (x,y) in clip:
            continue

        if x >= right or x < left or y >= bottom or y < top:
            continue

        p = pixels[(x,y)]
        if p != targetcolor:
            if p[3] > tolerance: # if not completly transparent
                # include border pixels
                clip.add( (x,y) )

            continue

        clip.add( (x,y) )

        thestack.add( (x + 1, y) ) # right
        thestack.add( (x - 1, y) ) # left
        thestack.add( (x, y + 1) ) # down
        thestack.add( (x, y - 1) ) # up

    return clip

# from itertools import chain

def floodfill(pixels, bbox, origin=None, targetcolor=(255, 255, 255, 255), tolerance=0, include_border_pixels=True):
    """Flood Fill at origin using a stack.
    Returns a set of pixels that were filled.

    :param pixels: sequence of pixels for a lines_image
    :param bbox: Bounding box to stay within
    :param origin: Point to floodfill at. Defaults to left, top of bbox.
    :param targetcolor: The Target color pixel with alpha.
    :param tolerance: Fuzziness when filling in.
    """
    left, top, right, bottom = bbox
    if origin is None:
        origin = (left, top)

    thestack = set()
    thestack.add(origin)
    clip = set()
    skips = set()

    def has_value(x, y):
        try:
            p = pixels[(x, y)]
        except IndexError:
            return False
        if p != targetcolor:
            if p[3] > tolerance:  # if not completly transparent
                return True
        return False

    while len(thestack) != 0:
        x, y = thestack.pop()

        if (x, y) in clip:
            continue

        if x >= right or x < left or y >= bottom or y < top:
            continue

        p = pixels[(x, y)]
        pixel_right = (x + 1, y)
        pixel_left = (x - 1, y)
        pixel_down = (x, y + 1)
        pixel_up = (x, y - 1)
        if p != targetcolor:
            # if not completly transparent and not already skipped
            if include_border_pixels and p[3] > tolerance and (x, y) not in skips:
                # include border pixels
                clip.add((x, y))

                if has_value(*pixel_right):
                    clip.add(pixel_right)
                if has_value(*pixel_left):
                    clip.add(pixel_left)
                if has_value(*pixel_down):
                    clip.add(pixel_down)
                if has_value(*pixel_up):
                    clip.add(pixel_up)

                pixel_right_up = (x + 1, y - 1)
                pixel_right_down = (x + 1, y + 1)
                pixel_left_up = (x - 1, y - 1)
                pixel_left_down = (x - 1, y + 1)
                for extend_pixel in [pixel_right_up, pixel_right_down, pixel_left_up, pixel_left_down]:
                    if has_value(*extend_pixel):
                        clip.add(extend_pixel)
                        skips.add(extend_pixel)

                # Could extend it further by grabbing all the surrounding
                # pixels. Not doing this as it is mostly a bad idea since only
                # really want the diagonal pixels.
                #
                # extend = 4
                # tl = (x - int(extend / 2), y - int(extend / 2))
                # xr = range(tl[0], tl[0] + extend + 1)
                # yr = range(tl[1], tl[1] + extend + 1)
                # for extend_pixel in chain.from_iterable(map(lambda i: zip(xr, [yr[i]] * (extend + 1)), range(extend + 1))):
                #     if has_value(*extend_pixel):
                #         clip.add(extend_pixel)
                #         skips.add(extend_pixel)

            continue

        clip.add((x, y))

        thestack.add(pixel_right)
        thestack.add(pixel_left)
        thestack.add(pixel_down)
        thestack.add(pixel_up)

    return clip

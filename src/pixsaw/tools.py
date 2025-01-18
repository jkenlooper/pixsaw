def floodfill(pixels, bbox, origin=None, targetcolor=(255, 255, 255, 255), tolerance=0, include_border_pixels=True, clip_max=50_000_000):
    """Flood Fill at origin.
    Returns a list of pixels that were filled along with farthest right and bottom pixel positions.

    :param pixels: sequence of pixels for a lines_image
    :param bbox: Bounding box to stay within
    :param origin: Point to floodfill at. Defaults to left, top of bbox.
    :param targetcolor: The Target color pixel with alpha.
    :param tolerance: Fuzziness when filling in.
    :param include_border_pixels: Include border pixels
    :param clip_max: Maximum pixels to flood
    """
    left, top, right, bottom = bbox
    if origin is None:
        origin = (left, top)

    clip = list()
    clip_left, clip_top, clip_right, clip_bottom = (0, 0, 0, 0)
    border = set()

    # Pulled from Pillow ImageDraw.floodfill
    x, y = origin
    try:
        p = pixels[origin]
    except (ValueError, IndexError):
        return (clip, (clip_left, clip_top, clip_right, clip_bottom))

    if p == targetcolor:
        return (clip, (clip_left, clip_top, clip_right, clip_bottom))

    clip.append(origin)

    clip_left, clip_top, clip_right, clip_bottom = (x, y, max(clip_right, x), max(clip_bottom, y))

    edge = {origin}
    # use a set to keep record of current and previous edge pixels
    # to reduce memory consumption
    full_edge = set()
    while edge:
        new_edge = set()
        for x, y in edge:  # 4 adjacent method
            for s, t in (
                    (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1),
            ):
                adjacent = (s, t)
                # If already processed, or if a coordinate is outside of bbox, skip
                if adjacent in full_edge or adjacent in border or s > right or s < left or t > bottom or t < top:
                    continue
                try:
                    p = pixels[adjacent]
                except (ValueError, IndexError):
                    pass
                else:
                    full_edge.add(adjacent)
                    if p == targetcolor:
                        clip.append(adjacent)
                        clip_left, clip_top, clip_right, clip_bottom = (min(clip_left, s), min(clip_top, t), max(clip_right, s), max(clip_bottom, t))

                        new_edge.add(adjacent)
                    elif include_border_pixels and p[3] > tolerance:  # not transparent and is border color
                        clip.append(adjacent)
                        clip_left, clip_top, clip_right, clip_bottom = (min(clip_left, s), min(clip_top, t), max(clip_right, s), max(clip_bottom, t))
                        border.add(adjacent)
                        # Extend to adjacent pixels when including the border
                        # pixels. This helps with getting a smoother edge on
                        # pieces.
                        # Adding the diagonal adjacent pixels increases the risk
                        # of joining two pieces if the border is too faint.
                        for a, b in (
                            (s + 1, t), (s - 1, t), (s, t + 1), (s, t - 1),
                            (s + 1, t + 1), (s - 1, t - 1), (s - 1, t + 1), (s + 1, t - 1),
                        ):
                            border_adjacent = (a, b)
                            if border_adjacent in full_edge or border_adjacent in border or a > right or a < left or b > bottom or b < top:
                                continue
                            try:
                                d = pixels[border_adjacent]
                            except (ValueError, IndexError):
                                pass
                            else:
                                if d != targetcolor and d[3] > tolerance:  # not transparent and is border color
                                    clip.append(border_adjacent)
                                    clip_left, clip_top, clip_right, clip_bottom = (min(clip_left, a), min(clip_top, b), max(clip_right, a), max(clip_bottom, b))
                                    border.add(border_adjacent)

        full_edge = edge  # discard pixels processed
        edge = new_edge

        if len(clip) > clip_max:
            # Avoid running out of memory for extra large pieces.
            break


    return (clip, (clip_left, clip_top, clip_right, clip_bottom))

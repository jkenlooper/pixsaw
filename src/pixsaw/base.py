from builtins import range
from builtins import object
import os.path
from os import makedirs
from glob import glob
import json
import logging
from random import shuffle
import base64
# import time

from PIL import Image
from PIL import ImageFilter

from pixsaw.tools import floodfill


BLEED = 2
HALF_BLEED = BLEED * 0.5

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class HandlerError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Handler(object):

    mask_prefix = "m-"
    piece_prefix = "p-"
    no_mask_prefix = "n-"

    def __init__(self, output_dir, lines_image, mask_dir="", raster_dir="", jpg_dir="", include_border_pixels=True, no_mask_raster_dir="", floodfill_min=400, floodfill_max=50_000_000):
        """Handler constructor
        Fills an output directory with the generated masks based on
        lines drawn on an image.  Skips creating masks if output directory is
        not empty.  Raises an error if lines_image does not match existing one
        (if output directory is not empty).

        :param output_dir: Output to this directory
        :param lines_image: Path to the lines image
        """
        makedirs(output_dir, exist_ok=True)
        if not os.path.isdir(output_dir):
            raise HandlerError("output directory is not a directory")

        original_lines_image = os.path.join(output_dir, os.path.basename(lines_image))

        self._floodfill_min = floodfill_min
        self._floodfill_max = floodfill_max

        self._lines_image = lines_image
        self._output_dir = output_dir
        self._mask_dir = os.path.join(output_dir, mask_dir)
        self._raster_dir = os.path.join(output_dir, raster_dir)
        self._no_mask_raster_dir = os.path.join(output_dir, no_mask_raster_dir)
        self._jpg_dir = os.path.join(output_dir, jpg_dir)
        if not os.path.isfile(original_lines_image):
            masks = self._generate_masks(include_border_pixels)
            with open(os.path.join(self._output_dir, "masks.json"), "w") as masks_json_file:
                json.dump(masks, masks_json_file)

    def _generate_masks(self, include_border_pixels):
        """Create each mask and return masks dictionary"""
        # starting at 0,0 and scanning each pixel on the row for a white pixel.
        # When found a white pixel floodfill it and create a mask file in
        # output dir.  Replace flooded pixels with transparent pixels and
        # continue.
        # No warning about possible DecompressionBombWarning since the image
        # being used is trusted.
        Image.MAX_IMAGE_PIXELS = None
        im = Image.open(self._lines_image).convert("RGBA")

        lines_image_name = os.path.basename(self._lines_image)
        im.save(os.path.join(self._output_dir, lines_image_name))

        pixels = im.load()
        bbox = im.getbbox()
        left, top, right, bottom = bbox
        width, height = im.size
        im.close()

        # scan line by line for pixels that are not transparent
        targetcolor = (255, 255, 255, 255)
        masks = {}
        #start = time.perf_counter()
        for row in range(top, bottom):
            for col in range(left, right):
                if pixels[(col, row)][3] > 0:
                    (mask_pixels, mask_pixels_bbox) = floodfill(pixels, bbox, (col, row), targetcolor=targetcolor, include_border_pixels=include_border_pixels, clip_max=self._floodfill_max)
                    if len(mask_pixels) == 0:
                        continue
                    (mask_pixels_left, mask_pixels_top, mask_pixels_right, mask_pixels_bottom) = mask_pixels_bbox

                    # If the mask_pixels are not big enough merge to the next one that may be.
                    sub_flood = False  # for breaking out of the for loops
                    if len(mask_pixels) < self._floodfill_min:  # and len(mask_pixels) > 10:
                        logger.info(f"{len(mask_pixels)=}")
                        mask_pixels_set = set(mask_pixels)

                        sub_flood_edge = {(col, row)}
                        sub_flood_full_edge = set()
                        while sub_flood_edge:
                            sub_flood_new_edge = set()
                            for x, y in sub_flood_edge:  # 4 adjacent method
                                if sub_flood:
                                    break
                                for s, t in (
                                    (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1),
                                ):

                                    if s >= right or t >= bottom:
                                        sub_flood = True
                                        break
                                    adjacent = (s, t)
                                    if adjacent in sub_flood_full_edge or s >= right or s < left or t >= bottom or t < top:
                                        continue
                                    try:
                                        p = pixels[adjacent]
                                    except (ValueError, IndexError):
                                        pass
                                    else:
                                        sub_flood_full_edge.add(adjacent)
                                        sub_flood_new_edge.add(adjacent)
                                        if adjacent not in mask_pixels_set and p[3] != 0:
                                            (extend_mask_pixels, mask_pixels_bbox) = floodfill(
                                                pixels, bbox, adjacent,
                                                targetcolor=targetcolor,
                                                include_border_pixels=include_border_pixels,
                                                clip_max=self._floodfill_max,
                                            )
                                            if len(extend_mask_pixels) == 0:
                                                continue
                                            mask_pixels_left = min(mask_pixels_left, mask_pixels_bbox[0])
                                            mask_pixels_top = min(mask_pixels_top, mask_pixels_bbox[1])
                                            mask_pixels_right = max(mask_pixels_right, mask_pixels_bbox[2])
                                            mask_pixels_bottom = max(mask_pixels_bottom, mask_pixels_bbox[3])
                                            mask_pixels.extend(extend_mask_pixels)
                                            if len(mask_pixels) >= self._floodfill_min:
                                                sub_flood = True
                                                break
                                            else:
                                                extend_mask_pixels_set = set(extend_mask_pixels)
                                                mask_pixels_set.update(extend_mask_pixels_set)
                            sub_flood_full_edge = sub_flood_edge  # discard pixels processed
                            sub_flood_edge = sub_flood_new_edge

                    if len(mask_pixels) >= self._floodfill_min or sub_flood:
                        mask_id = "_".join(map(str, (col, row, mask_pixels_right, mask_pixels_bottom)))

                        mask_pixels_width = (mask_pixels_right - mask_pixels_left) + 1
                        mask_pixels_height = (mask_pixels_bottom - mask_pixels_top) + 1
                        pixel_seq = [
                            0
                            for x in range(0, (mask_pixels_width * mask_pixels_height))
                        ]

                        for (x, y) in mask_pixels:
                            m_x = x - mask_pixels_left
                            m_y = y - mask_pixels_top
                            p_index = (m_y * mask_pixels_width) + m_x
                            pixel_seq[p_index] = 1 if pixels[(x, y)][3] != 0 else 0
                            pixels[(x, y)] = (0, 0, 0, 0)  # clear the pixel

                        floodmaskimg = Image.new(
                            "1",
                            (mask_pixels_width, mask_pixels_height),
                            0,
                        )
                        floodmaskimg.putdata(pixel_seq)
                        floodmaskimg.save(
                            os.path.join(
                                self._mask_dir, f"{self.mask_prefix}{mask_id}.bmp"
                            )
                        )
                        floodmaskimg.close()

                        m_bbox = (
                            mask_pixels_left,
                            mask_pixels_top,
                            mask_pixels_right + 1,
                            mask_pixels_bottom + 1,
                        )
                        # Save the mask bbox
                        masks[mask_id] = m_bbox

        #stop = time.perf_counter()
        #logger.info(f"masks {(stop - start):.5f}")
        return masks

    def process(self, image, exclude_size=(None,None)):
        """Cut up the image based on the saved masks generated from the
        lines_image.

        :param image: Path to image that will be cut
        """
        im = Image.open(image)
        width, height = im.size
        with open(os.path.join(self._output_dir, "masks.json"), "r") as masks_json_file:
            masks = json.load(masks_json_file)
        piece_id_to_mask = {}
        pieces = {}
        mask_files = glob(os.path.join(self._mask_dir, f"{self.mask_prefix}*.bmp"))
        # Shuffle the mask files so it isn't easy to guess the ordering
        shuffle(mask_files)
        for (mask_count, mask_file) in enumerate(mask_files):
            maskimg = Image.open(mask_file)

            if exclude_size[0] or exclude_size[1]:
                maskimg_width, maskimg_height = maskimg.size
                if exclude_size[0] and maskimg_width >= exclude_size[0]:
                    maskimg.close()
                    continue
                if exclude_size[1] and maskimg_height >= exclude_size[1]:
                    maskimg.close()
                    continue

            maskname = os.path.basename(mask_file)
            mask_id = os.path.splitext(maskname)[0][len(self.mask_prefix):]
            piece_id_to_mask[mask_count] = mask_id
            piecename = f"{self.mask_prefix}{mask_count}"
            bbox = masks.get(mask_id)
            bbox_with_padding = list(range(0, 4))
            bbox_with_padding[0] = bbox[0] - int(HALF_BLEED)
            bbox_with_padding[1] = bbox[1] - int(HALF_BLEED)
            bbox_with_padding[2] = bbox[2] + int(HALF_BLEED)
            bbox_with_padding[3] = bbox[3] + int(HALF_BLEED)
            piece_with_padding = im.crop(bbox_with_padding)
            piece = im.crop(bbox)
            transparent_blank = Image.new("RGBA", piece.size, (0, 0, 0, 0))
            no_mask_blank = Image.new("RGBA", piece.size, (0, 0, 0))
            black_blank_with_padding = Image.new("RGB", piece_with_padding.size, (0, 0, 0))
            maskimg_with_padding = black_blank_with_padding.copy()
            maskimg_with_padding.paste(maskimg, box=(int(HALF_BLEED), int(HALF_BLEED)))
            if BLEED != 0:
                maskimg_with_padding = maskimg_with_padding.convert("L")
                maskimg_with_padding = maskimg_with_padding.filter(ImageFilter.BoxBlur(radius=int(HALF_BLEED)))
                maskimg_with_padding = maskimg_with_padding.point(lambda x: 255 if x > 1 else 0)
            maskimg_with_padding = maskimg_with_padding.convert("1")
            maskimg_with_padding.save(os.path.join(self._mask_dir, f"{self.mask_prefix}{mask_id}-padding.bmp"))
            black_blank_with_padding.paste(piece_with_padding, box=(0, 0), mask=maskimg_with_padding)
            transparent_blank.paste(piece, box=(0, 0), mask=maskimg)
            no_mask_blank.paste(piece, box=(0, 0))
            piece_with_padding.close()
            maskimg_with_padding.close()
            maskimg.close()
            transparent_blank.save(
                os.path.join(self._raster_dir, f"{self.piece_prefix}{piecename}.png")
            )
            transparent_blank.close()
            no_mask_blank.save(
                os.path.join(self._no_mask_raster_dir, f"{self.no_mask_prefix}{piecename}.png")
            )
            no_mask_blank.close()
            black_blank_with_padding.save(
                os.path.join(
                    self._jpg_dir,
                    f"{self.piece_prefix}{piecename}.jpg",
                )
            )
            black_blank_with_padding.close()

            # Copy the bbox from mask to pieces dict which will now have 'shuffled' int id's
            pieces[mask_count] = bbox

        im.close()

        # Write new pieces.json
        with open(os.path.join(self._output_dir, "pieces.json"), "w") as pieces_json_file:
            json.dump(pieces, pieces_json_file)
        with open( os.path.join(self._output_dir, "piece_id_to_mask.json"), "w") as piece_id_to_mask_json_file:
            json.dump(piece_id_to_mask, piece_id_to_mask_json_file)

from builtins import range
from builtins import object
import os.path
from glob import glob
import json
import logging
from random import shuffle
import base64
# import time

from PIL import Image

from pixsaw.tools import floodfill

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class HandlerError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Handler(object):

    mask_prefix = "m-"
    piece_prefix = "p-"

    def __init__(self, output_dir, lines_image, mask_dir="", raster_dir="", jpg_dir=""):
        """Handler constructor
        Fills an output directory with the generated masks based on
        lines drawn on an image.  Skips creating masks if output directory is
        not empty.  Raises an error if lines_image does not match existing one
        (if output directory is not empty).

        :param output_dir: Output to this directory
        :param lines_image: Path to the lines image
        """
        if not os.path.isdir(output_dir):
            raise HandlerError("output directory is not a directory")

        original_lines_image = os.path.join(output_dir, os.path.basename(lines_image))

        self._lines_image = lines_image
        self._output_dir = output_dir
        self._mask_dir = os.path.join(output_dir, mask_dir)
        self._raster_dir = os.path.join(output_dir, raster_dir)
        self._jpg_dir = os.path.join(output_dir, jpg_dir)
        if not os.path.isfile(original_lines_image):
            self._generate_masks()

    def _generate_masks(self):
        """Create each mask and save in output dir"""
        # starting at 0,0 and scanning each pixel on the row for a white pixel.
        # When found a white pixel floodfill it and create a mask file in
        # output dir.  Replace flooded pixels with transparent pixels and
        # continue.
        im = Image.open(self._lines_image).convert("RGBA")

        lines_image_name = os.path.basename(self._lines_image)
        im.save(os.path.join(self._output_dir, lines_image_name))

        pixels = im.load()
        bbox = im.getbbox()
        left, top, right, bottom = bbox
        width, height = im.size
        im.close()
        mask_index = 0

        # scan line by line for pixels that are not transparent
        masks = {}
        for row in range(top, bottom):
            for col in range(left, right):
                if pixels[(col, row)][3] > 0:
                    # start = time.perf_counter()
                    mask_pixels = floodfill(pixels, bbox, (col, row))
                    # stop = time.perf_counter()
                    # If the mask_pixels are not big enought merge to the next one that may be.
                    if True:  # TODO: merge small masks
                        if len(mask_pixels) < 100: # and len(mask_pixels) > 10:
                            sub_flood = False  # for breaking out of the for loops
                            for subrow in range(row, min(row + 20, bottom)):
                                if sub_flood:
                                    break
                                for subcol in range(col, min(col + 20, right)):
                                    if (subcol, subrow) not in mask_pixels and pixels[
                                        (subcol, subrow)
                                    ][3] > 0:
                                        mask_pixels.update(floodfill(
                                            pixels, bbox, (subcol, subrow)
                                        ))
                                        if len(mask_pixels) >= 100:
                                            sub_flood = True
                                            break
                    if len(mask_pixels) >= 100:
                        # logger.info(f"floodfill {stop - start}")
                        # Use base64 of the mask_index to hint that the cut
                        # piece filename which uses base10 does not correlate
                        # with the base64 mask file name.
                        mask_id = (
                            base64.urlsafe_b64encode(bytes(str(mask_index), 'utf8'))
                            .decode()
                            .replace("=", "")
                        )

                        # Create mask image and save under mask_id
                        # start = time.perf_counter()
                        maskimg = Image.new("1", (width, height), 0)
                        # stop = time.perf_counter()
                        # logger.info(f"init blank mask {stop - start}")

                        # start = time.perf_counter()
                        mask_pixels_top = bottom
                        mask_pixels_right = left
                        mask_pixels_bottom = top
                        mask_pixels_left = right
                        for (x, y) in mask_pixels:
                            mask_pixels_top = min(mask_pixels_top, y)
                            mask_pixels_right = max(mask_pixels_right, x)
                            mask_pixels_bottom = max(mask_pixels_bottom, y)
                            mask_pixels_left = min(mask_pixels_left, x)

                        mask_pixels_width = (mask_pixels_right - mask_pixels_left) + 1
                        mask_pixels_height = (mask_pixels_bottom - mask_pixels_top) + 1
                        pixel_seq = [
                            (0, 0, 0, 0)
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
                        maskimg.paste(floodmaskimg, (mask_pixels_left, mask_pixels_top))
                        floodmaskimg.close()

                        m_bbox = maskimg.getbbox()
                        # stop = time.perf_counter()
                        # logger.info(f"flood mask {stop - start}")

                        # start = time.perf_counter()
                        maskimg = maskimg.crop(m_bbox)
                        maskimg.save(
                            os.path.join(
                                self._mask_dir, f"{self.mask_prefix}{mask_id}.bmp"
                            )
                        )
                        # stop = time.perf_counter()
                        # logger.info(f"save mask {stop - start}")
                        maskimg.close()

                        # Save the mask bbox
                        masks[mask_id] = m_bbox
                        mask_index = mask_index + 1

        masks_json_file = open(os.path.join(self._output_dir, "masks.json"), "w")
        json.dump(masks, masks_json_file)
        masks_json_file.close()

    def process(self, image):
        """Cut up the image based on the saved masks generated from the
        lines_image.

        :param image: Path to image that will be cut
        """
        im = Image.open(image)
        width, height = im.size
        masks_json_file = open(os.path.join(self._output_dir, "masks.json"), "r")
        masks = json.load(masks_json_file)
        piece_id_to_mask = {}
        pieces = {}
        mask_files = glob(os.path.join(self._mask_dir, f"{self.mask_prefix}*.bmp"))
        # Shuffle the mask files so it isn't easy to guess the ordering
        shuffle(mask_files)
        for (mask_count, mask_file) in enumerate(mask_files):
            maskname = os.path.basename(mask_file)
            mask_id = os.path.splitext(maskname)[0][len(self.mask_prefix) :]
            piece_id_to_mask[mask_count] = mask_id
            piecename = f"{self.mask_prefix}{mask_count}.png"
            piece = im.copy()
            piece = piece.crop(masks.get(mask_id))
            piece_width, piece_height = piece.size
            blank = Image.new("RGBA", (piece_width, piece_height), (0, 0, 0, 0))
            maskimg = Image.open(mask_file)
            blank.paste(piece, box=(0, 0), mask=maskimg)
            piece.close()
            maskimg.close()
            blank.save(
                os.path.join(self._raster_dir, f"{self.piece_prefix}{piecename}")
            )
            jpgpiece = blank.convert("RGB")
            blank.close()
            jpgpiece.save(
                os.path.join(
                    self._jpg_dir,
                    "%s%s.jpg" % (self.piece_prefix, os.path.splitext(piecename)[0]),
                )
            )
            jpgpiece.close()

            # Copy the bbox from mask to pieces dict which will now have 'shuffled' int id's
            pieces[mask_count] = masks.get(mask_id)

        im.close()

        # Write new pieces.json
        pieces_json_file = open(os.path.join(self._output_dir, "pieces.json"), "w")
        json.dump(pieces, pieces_json_file)
        piece_id_to_mask_json_file = open(
            os.path.join(self._output_dir, "piece_id_to_mask.json"), "w"
        )
        json.dump(piece_id_to_mask, piece_id_to_mask_json_file)

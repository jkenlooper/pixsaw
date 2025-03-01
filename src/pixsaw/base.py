from builtins import range
from builtins import object
import os.path
from os import makedirs, mkdir
from glob import glob
import json
import logging
from random import shuffle, choice
import base64
from pathlib import Path
# import time

from PIL import Image
from PIL import ImageFilter

from pixsaw.tools import floodfill


BLEED = 2
HALF_BLEED = int(BLEED * 0.5)

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
    mask_rotated_prefix = "r-"
    piece_prefix = "p-"
    no_mask_prefix = "n-"

    def __init__(self, output_dir, lines_image, mask_dir="", mask_rotated_dir="", raster_dir="", jpg_dir="", include_border_pixels=True, no_mask_raster_dir="", floodfill_min=400, floodfill_max=50_000_000, rotate=()):
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

        self._rotate=rotate

        self._lines_image = lines_image
        self._output_dir = output_dir
        self._mask_dir = os.path.join(output_dir, mask_dir)
        self._mask_rotated_dir = os.path.join(output_dir, mask_rotated_dir)
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
                    if len(mask_pixels) < self._floodfill_min and len(mask_pixels) > 10:
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
                        # Create rotated mask
                        random_rotate = choice(self._rotate) if self._rotate else 0
                        if random_rotate:
                            # Only need to create rotated mask files if the mask is rotated.
                            maskimg_rotate = floodmaskimg.rotate(random_rotate, expand=True)
                            before_cropped_size = maskimg_rotate.size
                            bbox_crop = maskimg_rotate.getbbox(alpha_only=False)
                            maskimg_rotate = maskimg_rotate.crop(bbox_crop)
                            after_cropped_size = maskimg_rotate.size
                            center_x = round(((before_cropped_size[0] / 2) - bbox_crop[0]) / after_cropped_size[0], 5)
                            center_y = round(((before_cropped_size[1] / 2) - bbox_crop[1]) / after_cropped_size[1], 5)
                            center_x_offset = round(((after_cropped_size[0] * center_x) - (mask_pixels_width / 2)) * -1, 1)
                            center_y_offset = round(((after_cropped_size[1] * center_y) - (mask_pixels_height / 2)) * -1, 1)
                            maskimg_rotate.save(
                                os.path.join(self._mask_rotated_dir, f"{self.mask_rotated_prefix}{mask_id}.bmp")
                            )
                            maskimg_rotate.close()
                        else:
                            center_x = 0.5
                            center_y = 0.5
                            center_x_offset = 0
                            center_y_offset = 0
                            bbox_crop = floodmaskimg.getbbox(alpha_only=False)

                        floodmaskimg.close()

                        # Using a tuple here with this specific ordering for
                        # optimal storage and backwards compatibility. Most
                        # applications using pixsaw can expose these values in
                        # a more user friendly way if necessary.
                        m_bbox = (
                            mask_pixels_left,
                            mask_pixels_top,
                            mask_pixels_right + 1,
                            mask_pixels_bottom + 1,
                            random_rotate,
                            center_x,
                            center_y,
                            center_x_offset,
                            center_y_offset,
                        ) + bbox_crop
                        # Save the mask bbox
                        masks[mask_id] = m_bbox

        #stop = time.perf_counter()
        #logger.info(f"masks {(stop - start):.5f}")
        return masks

    def process(self, images, exclude_size=(None,None)):
        """Cut up the images based on the saved masks generated from the
        lines_image.
        :param images: Paths to images that will be cut
        """
        im_sides = tuple(map(Image.open, images))
        width, height = im_sides[0].size
        if any(map(lambda im: (width, height) != im.size, im_sides)):
            raise HandlerError("All images used must be the same size in width and height.")
        for image_index, _ in enumerate(im_sides):
            for d in (self._raster_dir, self._no_mask_raster_dir, self._jpg_dir):
                Path(d).joinpath(f"image-{image_index}").mkdir(exist_ok=True)
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
            bbox = tuple(masks.get(mask_id))
            bbox_with_padding = (
                bbox[0] - HALF_BLEED,
                bbox[1] - HALF_BLEED,
                bbox[2] + HALF_BLEED,
                bbox[3] + HALF_BLEED,
            )

            random_rotate = bbox[4]
            bbox_after_rotate = tuple(bbox[9:13])

            maskimg_with_padding = Image.new("RGB", (bbox_with_padding[2] - bbox_with_padding[0], bbox_with_padding[3] - bbox_with_padding[1]), (0, 0, 0))
            maskimg_with_padding.paste(maskimg, box=(HALF_BLEED, HALF_BLEED))
            if BLEED != 0:
                maskimg_with_padding = maskimg_with_padding.convert("L")
                maskimg_with_padding = maskimg_with_padding.filter(ImageFilter.BoxBlur(radius=HALF_BLEED))
                maskimg_with_padding = maskimg_with_padding.point(lambda x: 255 if x > 1 else 0)
            maskimg_with_padding = maskimg_with_padding.convert("1")
            maskimg_with_padding.save(os.path.join(self._mask_dir, f"{self.mask_prefix}{mask_id}-padding.bmp"))

            for image_index, im in enumerate(im_sides):
                piece_with_padding = im.crop(bbox_with_padding)
                piece = im.crop(bbox[:4])

                black_blank_with_padding = Image.new("RGB", piece_with_padding.size, (0, 0, 0))
                black_blank_with_padding.paste(piece_with_padding, box=(0, 0), mask=maskimg_with_padding)

                transparent_blank = Image.new("RGBA", piece.size, (0, 0, 0, 0))
                transparent_blank.paste(piece, box=(0, 0), mask=maskimg)
                no_mask_blank = Image.new("RGBA", piece.size, (0, 0, 0))
                no_mask_blank.paste(piece, box=(0, 0))

                piece.close()
                piece_with_padding.close()

                if random_rotate:
                    transparent_blank = transparent_blank.rotate(random_rotate, expand=True)
                    no_mask_blank = no_mask_blank.rotate(random_rotate, expand=True)
                    black_blank_with_padding = black_blank_with_padding.rotate(random_rotate, expand=True)
                    transparent_blank = transparent_blank.crop(bbox_after_rotate)
                    no_mask_blank = no_mask_blank.crop(bbox_after_rotate)
                    black_blank_with_padding = black_blank_with_padding.crop(bbox_after_rotate)

                transparent_blank.save(
                    os.path.join(self._raster_dir, f"image-{image_index}", f"{self.piece_prefix}{piecename}.png")
                )
                transparent_blank.close()
                no_mask_blank.save(
                    os.path.join(self._no_mask_raster_dir, f"image-{image_index}", f"{self.no_mask_prefix}{piecename}.png")
                )
                no_mask_blank.close()
                black_blank_with_padding.save(
                    os.path.join(
                        self._jpg_dir,
                        f"image-{image_index}",
                        f"{self.piece_prefix}{piecename}.jpg",
                    )
                )
                black_blank_with_padding.close()

            maskimg.close()
            maskimg_with_padding.close()
            # Copy the bbox from mask to pieces dict which will now have 'shuffled' int id's
            pieces[mask_count] = bbox

        for im in im_sides:
            im.close()

        # Write new pieces.json
        with open(os.path.join(self._output_dir, "pieces.json"), "w") as pieces_json_file:
            json.dump(pieces, pieces_json_file)
        with open( os.path.join(self._output_dir, "piece_id_to_mask.json"), "w") as piece_id_to_mask_json_file:
            json.dump(piece_id_to_mask, piece_id_to_mask_json_file)

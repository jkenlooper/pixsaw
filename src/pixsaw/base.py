from builtins import range
from builtins import object
import os.path
from glob import glob
import json
import logging
import uuid

from PIL import Image

from pixsaw.tools import floodfill

class HandlerError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Handler(object):

    mask_prefix = 'm-'
    piece_prefix = 'p-'

    def __init__(self, output_dir, lines_image, mask_dir='', raster_dir='', jpg_dir=''):
        """Handler constructor
        Fills an output directory with the generated masks based on
        lines drawn on an image.  Skips creating masks if output directory is
        not empty.  Raises an error if lines_image does not match existing one
        (if output directory is not empty).

        :param output_dir: Output to this directory
        :param lines_image: Path to the lines image
        """
        if not os.path.isdir(output_dir):
            raise HandlerError('output directory is not a directory')

        original_lines_image = os.path.join(
                output_dir,
                os.path.basename(lines_image))

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
        logging.debug("bbox %s, %s, %s, %s" % bbox)

        #scan line by line for pixels that are not transparent
        masks = {}
        for row in range(top, bottom):
            for col in range(left, right):
                if pixels[(col,row)][3] > 0:
                    mask_pixels = floodfill(pixels, bbox, (col, row))
                    # If the mask_pixels are not big enought merge to the next one that may be.
                    if False: # TODO: merge small masks
                        if len(mask_pixels) < 100 and len(mask_pixels) > 1:
                            sub_flood = False # for breaking out of the for loops
                            for subrow in range(row, bottom):
                                if sub_flood:
                                    break
                                for subcol in range(left, right):
                                    if (subcol, subrow) not in mask_pixels and pixels[(subcol,subrow)][3] > 0:
                                        adjacent_flood = floodfill(pixels, bbox, (subcol, subrow))
                                        if len(adjacent_flood) > 100:
                                            mask_pixels.update(adjacent_flood)
                                            sub_flood = True
                                            break
                    if len(mask_pixels) >= 100:
                        # Use a uuid here to avoid sequentially numbering the masks.
                        mask_id = uuid.uuid4().hex

                        # Create mask image and save under mask_id
                        maskimg = Image.new("RGBA", (width, height), (0,0,0,0))
                        pixel_seq = [(0,0,0,0) for x in range(0, (width*height))]
                        for (x, y) in mask_pixels:
                            p_index = (y*width) + x
                            black_pixel_with_alpha = (0,0,0, pixels[(x,y)][3])
                            pixel_seq[p_index] = black_pixel_with_alpha
                            pixels[(x,y)] = (0,0,0,0) # clear the pixel
                        maskimg.putdata( pixel_seq )
                        m_bbox = maskimg.getbbox()
                        logging.debug("new mask: %s" % mask_id)
                        maskimg.save(
                                os.path.join(self._mask_dir,
                                '%s%s.png' % (self.mask_prefix, mask_id)) )
                        maskimg.close()

                        #TODO: create a svg version of the mask using potrace?
                        # Save the mask bbox
                        masks[mask_id] = m_bbox

        masks_json_file = open(os.path.join( self._output_dir, 'masks.json'), 'w')
        json.dump(masks, masks_json_file)

    def process(self, image):
        """Cut up the image based on the saved masks generated from the
        lines_image.

        :param image: Path to image that will be cut
        """
        im = Image.open(image)
        width, height = im.size
        masks_json_file = open(os.path.join( self._output_dir, 'masks.json'), 'r')
        masks = json.load(masks_json_file)
        pieces = {}
        mask_count = 0

        # Rely on the glob sort ordering here to shuffle the piece int id's
        for mask in glob(os.path.join(self._mask_dir, '%s*.png' % self.mask_prefix)):
            piece = Image.new("RGBA", (width, height), (0,0,0,0))
            maskimg = Image.open(mask)
            maskname = os.path.basename(mask)
            piecename = "{0}{1}.png".format(self.mask_prefix, mask_count)
            mask_id = maskname[len(self.mask_prefix):maskname.find('.')]
            piece.paste(im, (0,0), maskimg)
            maskimg.close()
            logging.debug('crop %s' % masks.get(mask_id))
            piece = piece.crop(masks.get(mask_id))
            piece.save( os.path.join(self._raster_dir, '%s%s' %
                (self.piece_prefix, piecename)) )
            piece.save( os.path.join(self._jpg_dir, '%s%s.jpg' %
                (self.piece_prefix, os.path.splitext(piecename)[0])) )
            piece.close()

            # Copy the bbox from mask to pieces dict which will now have 'shuffled' int id's
            pieces[mask_count] = masks.get(mask_id)
            mask_count = mask_count + 1

        im.close()


        # Write new pieces.json
        pieces_json_file = open(os.path.join( self._output_dir, 'pieces.json'), 'w')
        json.dump(pieces, pieces_json_file)

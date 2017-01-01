import os.path
from glob import glob
import json
import logging

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
        masks_count = 0
        pieces = {}
        for row in xrange(top, bottom):
            for col in xrange(left, right):
                if pixels[(col,row)][3] > 0:
                    mask_pixels = floodfill(pixels, bbox, (col, row))
                    # If the mask_pixels are not big enought merge to the next one that may be.
                    if False: # TODO: merge small pieces
                        if len(mask_pixels) < 100 and len(mask_pixels) > 1:
                            sub_flood = False # for breaking out of the for loops
                            for subrow in xrange(row, bottom):
                                if sub_flood:
                                    break
                                for subcol in xrange(left, right):
                                    if (subcol, subrow) not in mask_pixels and pixels[(subcol,subrow)][3] > 0:
                                        adjacent_flood = floodfill(pixels, bbox, (subcol, subrow))
                                        if len(adjacent_flood) > 100:
                                            mask_pixels.update(adjacent_flood)
                                            sub_flood = True
                                            break
                    if len(mask_pixels) >= 100:
                        maskimg = Image.new("RGBA", (width, height), (0,0,0,0))
                        pixel_seq = [(0,0,0,0) for x in range(0, (width*height))]
                        for (x, y) in mask_pixels:
                            p_index = (y*width) + x
                            black_pixel_with_alpha = (0,0,0, pixels[(x,y)][3])
                            pixel_seq[p_index] = black_pixel_with_alpha
                            pixels[(x,y)] = (0,0,0,0) # clear the pixel
                        maskimg.putdata( pixel_seq )
                        m_bbox = maskimg.getbbox()
                        logging.debug("new mask: %s" % masks_count)
                        maskimg.save(
                                os.path.join(self._mask_dir,
                                '%s%s.png' % (self.mask_prefix, masks_count)) )
                        maskimg.close()

                        #TODO: create a svg version of the mask using potrace?
                        pieces[masks_count] = m_bbox
                        masks_count += 1
        piece_json_file = open(os.path.join( self._output_dir, 'pieces.json'), 'w')
        json.dump(pieces, piece_json_file)

    def process(self, image):
        """Cut up the image based on the saved masks generated from the
        lines_image.

        :param image: Path to image that will be cut
        """
        im = Image.open(image)
        width, height = im.size
        piece_json_file = open(os.path.join( self._output_dir, 'pieces.json'), 'r')
        pieces = json.load(piece_json_file)
        for mask in glob(os.path.join(self._mask_dir, '%s*.png' % self.mask_prefix)):
            piece = Image.new("RGBA", (width, height), (0,0,0,0))
            maskimg = Image.open(mask)
            maskname = os.path.basename(mask)
            mask_id = maskname[len(self.mask_prefix):maskname.find('.')]
            piece.paste(im, (0,0), maskimg)
            maskimg.close()
            logging.debug('crop %s' % pieces.get(mask_id))
            piece = piece.crop(pieces.get(mask_id))
            piece.save( os.path.join(self._raster_dir, '%s%s' %
                (self.piece_prefix, maskname)) )
            piece.save( os.path.join(self._jpg_dir, '%s%s.jpg' %
                (self.piece_prefix, os.path.splitext(maskname)[0])) )
            piece.close()
        im.close()

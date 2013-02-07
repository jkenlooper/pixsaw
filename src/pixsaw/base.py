
class Manager(object):

    def __init__(self, output_dir, lines_image):
        """Manager constructor

        :param output_dir: Output to this directory
        :param lines_image: Path to the lines image
        """
        # if output_dir is not empty and existing lines_image within dir is the
        # same then skip creating each mask

        self._generate_masks()

    def _generate_masks(self):
        """Create each mask and save in output dir"""

        # starting at 0,0 and scanning each pixel on the row for a white pixel.
        # When found a white pixel floodfill it and create a mask file in
        # output dir.  Replace flooded pixels with transparent pixels and
        # continue.

    def _floodpixel(self, point):
        """Flood fill at pixel point"""


    def process(self, image):
        """Cut up the image based on the saved masks generated from the
        lines_image.

        :param image: Path to image that will be cut
        """


floodfill 

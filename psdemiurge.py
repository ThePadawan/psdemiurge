#!/usr/bin/python
"""Converts character art from .psd format of stacked layers to multiple files
   of alpha-blended layers based on .json per-character configuration files."""

import argparse
import json
import logging
import os
import glob
from datetime import datetime
from PIL import Image
from psd_tools import PSDImage

LOG_LEVELS = {
    0: logging.CRITICAL,
    1: logging.ERROR,
    2: logging.INFO,
    3: logging.DEBUG
}

TIMESTAMP = ("# This file was autogenerated on {} by psdemiurge.py."
             " Manual changes will be lost.\n")

def get_character_json(filename):
    """Loads per-character configuration JSON struct from file."""
    with open(filename, 'r') as json_file:
        json_string = json_file.read()
    return json.loads(json_string)

def parse_args():
    """Parse console arguments."""
    parser = argparse.ArgumentParser(
        description="Process .psd + .json files into flattened images.")
    parser.add_argument(
        dest="target_folder",
        help="folder in which to look for .json files")
    parser.add_argument(
        "-v",
        "--verbosity",
        dest="verbosity",
        default=1,
        choices=LOG_LEVELS.keys(),
        type=int,
        help="how verbose should the output be, from 0=quiet to 3=debug")
    return parser.parse_args()


class PSDemiurge():
    """Main class: processes files in given folder."""

    def __init__(self):
        args = parse_args()

        self.create_logger(LOG_LEVELS[args.verbosity])

        self.logger.debug("Using target_folder '%s'", args.target_folder)
        self.target_folder = args.target_folder
        # rpy_path = "tbd"
        # self.rpy_file = open(rpy_path, 'w')


    def create_logger(self, level):
        """Create a logger with the specified log level."""

        self.logger = logging.getLogger('PSDemiurge')
        self.logger.setLevel(level)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(
            logging.Formatter("[%(levelname)s] %(message)s"))

        self.logger.addHandler(console_handler)


    def run(self):
        """Main method: processes files in given folder."""

        json_glob = os.path.join(os.path.abspath(self.target_folder), '*.json')

        filenames = [os.path.splitext(s)[0] for s in glob.glob(json_glob)]

        if len(filenames) < 1:
            self.logger.warning("No .json files found, aborting.")
            return

        self.logger.debug("Found %d .json files", len(filenames))

        for fname in filenames:
            if not os.path.isfile("{}.psd".format(fname)):
                self.logger.warning("No corresponding PSD found for file %s.json.", fname)

        if not os.path.exists(self.target_folder):
            self.logger.info("Target folder does not exist, creating it...")
            os.mkdir(self.target_folder)

        now = datetime.now()
        now_string = now.strftime("%a, %b %d %Y, %H:%M")
        self.logger.info("Using timestamp '%s'", now_string)

        # self.rpy_file.write(TIMESTAMP.format(now_string))
        for base_name in sorted(filenames):
            self.render_pngs(base_name)

    def render_pngs(self, base_name):
        """Renders separate pngs for every character and mood, and logs
           their location to .rpy file."""
        psd_name = "{}.psd".format(base_name)

        self.logger.info("Rendering images for %s", psd_name)

        if not os.path.exists(psd_name):
            return

        psd_image = PSDImage.load(psd_name)
        json_struct = get_character_json("{}.json".format(base_name))

        # self.rpy_file.write("# {}\n".format(base_name))

        for mood, layer_names in sorted(json_struct["moods"].items()):
            output_folder = os.path.join(self.target_folder, base_name)
            if not os.path.exists(output_folder):
                os.mkdir(output_folder)

            if not layer_names:
                self.logger.warning(
                    "Zero layers specified for '%s', skipping it.",
                    mood)
                continue

            output_filename = "{}_{}.png".format(base_name, mood)
            self.logger.info("Now saving %s", format(output_filename))


            output_image = self.combine_layers(psd_image, layer_names)

            output_image.save(os.path.join(output_folder, output_filename))

            #self.rpy_file.write(
            #    "image {0} {1} = Image(\"img/characters/{0}/{2}\""
            #    ", yanchor={3:.2f})\n"
            #    .format(
            #        base_name, mood, output_filename, json_struct["yanchor"]))

    def combine_layers(self, psd_image, layer_names):
        """Flattens layers with given names in given image into one image."""

        used_layers = [l for l in psd_image.layers if l.name in layer_names]
        used_layers.reverse()
        layer_images = [layer.as_PIL() for layer in used_layers]

        bounding_size = self.get_bounding_size(used_layers)
        self.logger.debug("Bounding size of all layers: %s", bounding_size)

        output_image = Image.new(layer_images[0].mode, bounding_size)

        for i in range(0, len(layer_images)):
            ith_image = layer_images[i]
            ith_layer = used_layers[i]

            self.logger.debug("Treating layer %s", ith_layer)
            self.logger.debug("layer bbox is %s", ith_layer.bbox)
            self.logger.debug("Treating image %s", ith_image)

            output_image.paste(
                ith_image,
                box=(ith_layer.bbox.x1, ith_layer.bbox.y1),
                mask=ith_image)

        return output_image

    def get_bounding_size(self, layers):
        """Get (width, height) of bbox of bboxes of given layers."""

        current_bbox = {"x1": 0, "y1": 0, "x2": 0, "y2": 0}
        self.logger.debug("Getting bounding size of layers %s", layers)
        for layer in layers:
            if layer.bbox.x1 < current_bbox["x1"]:
                current_bbox["x1"] = layer.bbox.x1
            if layer.bbox.y1 < current_bbox["y1"]:
                current_bbox["y1"] = layer.bbox.y1
            if layer.bbox.x2 > current_bbox["x2"]:
                current_bbox["x2"] = layer.bbox.x2
            if layer.bbox.y2 > current_bbox["y2"]:
                current_bbox["y2"] = layer.bbox.y2

        return (current_bbox["x2"] - current_bbox["x1"],
                current_bbox["y2"] - current_bbox["y1"])

if __name__ == '__main__':
    PSDemiurge().run()

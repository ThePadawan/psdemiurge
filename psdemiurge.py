#!/usr/bin/python
"""Converts character art from .psd format of stacked layers to multiple files
   of alpha-blended layers based on .json per-character configuration files."""

import json
import sys
import os
import glob
from datetime import datetime
from psd_tools import PSDImage

# TODO: Manage output based on verbosity
TIMESTAMP = ("# This file was autogenerated on {} by psdemiurge.py."
             " Manual changes will be lost.\n")

def get_character_json(filename):
    """Loads per-character configuration JSON struct from file."""
    with open(filename, 'r') as json_file:
        json_string = json_file.read()
    return json.loads(json_string)

class PSDemiurge():
    def __init__(self):
        self.image_path = os.path.join("..", "Eidolon", "game", "img",
                                       "characters")
        rpy_path = os.path.join("..", "Eidolon", "game",
                                "character_sprites.rpy")
        self.rpy_file = open(rpy_path, 'w')

    def run(self):
        filenames = [os.path.splitext(s)[0] for s in glob.glob("*.json")]

        for fname in filenames:
            if not os.path.isfile("{}.psd".format(fname)):
                print("No corresponding PSD found for file {}.json."
                      .format(fname), file=sys.stderr)

        if not os.path.exists(self.image_path):
            os.mkdir(self.image_path)

        now = datetime.now()
        now_string = now.strftime("%a, %b %d %Y, %H:%M")
        self.rpy_file.write(TIMESTAMP.format(now_string))
        for base_name in sorted(filenames):
            self.render_pngs(base_name)

    def render_pngs(self, base_name):
        """Renders separate pngs for every character and mood, and logs
           their location to .rpy file."""
        psd_name = "{}.psd".format(base_name)

        if not os.path.exists(psd_name):
            return

        psd_image = PSDImage.load(psd_name)
        json_struct = get_character_json("{}.json".format(base_name))

        self.rpy_file.write("# {}\n".format(base_name))

        for mood, layer_names in sorted(json_struct["moods"].items()):
            output_folder = os.path.join(self.image_path, base_name)
            if not os.path.exists(output_folder):
                os.mkdir(output_folder)
            output_filename = "{}_{}.png".format(base_name, mood)
            print("Now saving {}...".format(output_filename))
            output_full_filename = os.path.join(output_folder, output_filename)

            # TODO: Right now, this fails badly when a layer is not the same
            # size as the whole image. Can thankfully be ensured in
            # the original .psd.
            if layer_names:
                used_layers = [l for l in psd_image.layers if l.name in layer_names]
                used_layers.reverse()
                layer_images = [layer.as_PIL() for layer in used_layers]

                for i in range(1, len(layer_images)):
                    layer_images[0].paste(layer_images[i], layer_images[i])

                layer_images[0].save(output_full_filename)

            self.rpy_file.write(
                "image {0} {1} = Image(\"img/characters/{0}/{2}\""
                ", yanchor={3:.2f})\n"
                .format(
                    base_name, mood, output_filename, json_struct["yanchor"]))


if __name__ == '__main__':
    PSDemiurge().run()

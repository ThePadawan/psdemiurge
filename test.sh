#!/bin/sh
set -ev

chmod +x ./*.py
./psdemiurge.py -v 3 -i examples/ -o out.rpy

SHA1=`sha512sum examples/red_and_blue_layers_centered/red_and_blue_layers_centered_blue_then_red.png | awk -F ' ' '{ print $1 }'`
SHA2=`sha512sum examples/red_and_blue_layers_offset/red_and_blue_layers_offset_blue_then_red.png | awk -F ' ' '{ print $1 }'`

if [ "$SHA1" = "$SHA2" ]; then
  echo "SHA sums match, everything fine!"
else
  echo "SHA sums should be equal, but aren't!"
  echo $SHA1
  echo $SHA2
  exit 1
fi

# Pixsaw

Cuts an image up into multiple pieces by following pixel lines that contrast
with targeted piece color. _Most_ pixels are kept in the process since very fine
saw blades are used.

Try out by running the `pixsaw.sh` script that will prompt for necessary options
and run pixsaw inside a docker container. It will use the files in the examples
directory by default.

```bash
# Build and run using docker
./pixsaw.sh
```

## Installing

Requires:

* [Pillow](http://github.com/python-imaging/Pillow)

Install with pip in editable mode for developing and use virtualenv to isolate
python dependencies::

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```


## Usage

Running the `pixsaw` script will show some help.  It basically needs a
path to a directory to store the generated files, an image that shows where to
cut, and the image that should be cut into pieces.

Example

```bash
mkdir tmp-small-puzzle-example
pixsaw --dir tmp-small-puzzle-example --lines examples/small-puzzle-lines.png examples/320px-White_Spoon_Osteospermum.jpg
```

![The puzzle lines](https://github.com/jkenlooper/pixsaw/raw/main/examples/small-puzzle-lines.png)


![Image example](https://github.com/jkenlooper/pixsaw/raw/main/examples/320px-White_Spoon_Osteospermum.jpg)

Image from: http://en.wikipedia.org/wiki/File:White_Spoon_Osteospermum.JPG

The output (combined into one file with glue to better show it):

![Output of pixsaw](https://github.com/jkenlooper/pixsaw/raw/main/examples/pieces-combined-with-glue.png)

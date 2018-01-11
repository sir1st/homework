C:\Anaconda3\Lib\site-packages\PIL  
from PIL import ImagePalette   raw() *
image.new   *
open   *
resize  *
show    *
save    *
convert   *
getpixel   *
quantize   *
copy    *
load    *
_new     *
palette.getcolor   .copy   


from homework import Sjn_palette
import os
import sys 
import io
import warnings

USE_CFFI_ACCESS = hasattr(sys, 'pypy_version_info')
try:
    import cffi
    HAS_CFFI = True
except ImportError:
    HAS_CFFI = False

NONE = 0
MAX_IMAGE_PIXELS = int(1024 * 1024 * 1024 / 4 / 3)

# dithers
NONE = 0
NEAREST = 0
ORDERED = 1  # Not yet implemented
RASTERIZE = 2  # Not yet implemented
FLOYDSTEINBERG = 3  # default

# palettes/quantizers
WEB = 0
ADAPTIVE = 1

MEDIANCUT = 0
MAXCOVERAGE = 1
FASTOCTREE = 2

# resampling filters
NEAREST = NONE = 0
LANCZOS = ANTIALIAS = 1
BILINEAR = LINEAR = 2
BICUBIC = CUBIC = 3

# Registries

ID = []
OPEN = {}
MIME = {}
SAVE = {}
SAVE_ALL = {}
EXTENSION = {}

_MODEINFO = {
    # NOTE: this table will be removed in future versions.  use
    # getmode* functions or ImageMode descriptors instead.

    # official modes
    "1": ("L", "L", ("1",)),
    "L": ("L", "L", ("L",)),
    "I": ("L", "I", ("I",)),
    "F": ("L", "F", ("F",)),
    "P": ("RGB", "L", ("P",)),
    "RGB": ("RGB", "L", ("R", "G", "B")),
    "RGBX": ("RGB", "L", ("R", "G", "B", "X")),
    "RGBA": ("RGB", "L", ("R", "G", "B", "A")),
    "CMYK": ("RGB", "L", ("C", "M", "Y", "K")),
    "YCbCr": ("RGB", "L", ("Y", "Cb", "Cr")),
    "LAB": ("RGB", "L", ("L", "A", "B")),
    "HSV": ("RGB", "L", ("H", "S", "V")),
}
MODES = sorted(_MODEINFO.keys())

_initialized = 0


def preinit():
    "Explicitly load standard file format drivers."

    global _initialized
    if _initialized >= 1:
        return

    try:
        from PIL import BmpImagePlugin
    except ImportError:
        pass
    try:
        from PIL import GifImagePlugin
    except ImportError:
        pass
    try:
        from PIL import JpegImagePlugin
    except ImportError:
        pass
    try:
        from PIL import PpmImagePlugin
    except ImportError:
        pass
    try:
        from PIL import PngImagePlugin
    except ImportError:
        pass
#   try:
#       import TiffImagePlugin
#   except ImportError:
#       pass

    _initialized = 1


class Image(object):
   
    format = None
    format_description = None



    def __init__(self):
        # FIXME: take "new" parameters / other image?
        # FIXME: turn mode and size into delegating properties?
        self.im = None
        self.mode = ""
        self.size = (0, 0)
        self.palette = None
        self.info = {}
        self.category = NORMAL
        self.readonly = 0
        self.pyaccess = None

    def _new(self, im):
        new = Image()
        new.im = im
        new.mode = im.mode
        new.size = im.size
        if self.palette:
            new.palette = self.palette.copy()
        if im.mode == "P" and not new.palette:
            new.palette = ImagePalette.ImagePalette()
        try:
            new.info = self.info.copy()
        except AttributeError:
            # fallback (pre-1.5.2)
            new.info = {}
            for k, v in self.info:
                new.info[k] = v
        return new

    def _copy(self):
        self.load()
        self.im = self.im.copy()
        self.pyaccess = None
        self.readonly = 0

    def load(self):
        """
        Allocates storage for the image and loads the pixel data.  In
        normal cases, you don't need to call this method, since the
        Image class automatically loads an opened image when it is
        accessed for the first time. This method will close the file
        associated with the image.

        :returns: An image access object.
        """
        if self.im and self.palette and self.palette.dirty:
            # realize palette
            self.im.putpalette(*self.palette.getdata())
            self.palette.dirty = 0
            self.palette.mode = "RGB"
            self.palette.rawmode = None
            if "transparency" in self.info:
                if isinstance(self.info["transparency"], int):
                    self.im.putpalettealpha(self.info["transparency"], 0)
                else:
                    self.im.putpalettealphas(self.info["transparency"])
                self.palette.mode = "RGBA"

        if self.im:
            if HAS_CFFI and USE_CFFI_ACCESS:
                if self.pyaccess:
                    return self.pyaccess
                from homework import Sjn_access
                self.pyaccess = PyAccess.new(self, self.readonly)
                if self.pyaccess:
                    return self.pyaccess
            return self.im.pixel_access(self.readonly)    

    def convert(self, mode=None, matrix=None, dither=None,
                palette=WEB, colors=256):
        """
        The current version supports all possible conversions between
        "L", "RGB" and "CMYK." The **matrix** argument only supports "L"
        and "RGB".
        :param mode: The requested mode. 
        :param matrix: An optional conversion matrix.  If given, this
           should be 4- or 12-tuple containing floating point values.
        :param dither: Dithering method, used when converting from
           mode "RGB" to "P" or from "RGB" or "L" to "1".
           Available methods are NONE or FLOYDSTEINBERG (default).
        :param palette: Palette to use when converting from mode "RGB"
           to "P".  Available palettes are WEB or ADAPTIVE.
        :param colors: Number of colors to use for the ADAPTIVE palette.
           Defaults to 256.
        """

        if not mode:
            # determine default mode
            if self.mode == "P":
                self.load()
                if self.palette:
                    mode = self.palette.mode
                else:
                    mode = "RGB"
            else:
                return self.copy()

        self.load()

        if matrix:
            # matrix conversion
            if mode not in ("L", "RGB"):
                raise ValueError("illegal conversion")
            im = self.im.convert_matrix(mode, matrix)
            return self._new(im)

        if mode == "P" and self.mode == "RGBA":
            return self.quantize(colors)

        trns = None
        delete_trns = False
        # transparency handling
        if "transparency" in self.info and \
                self.info['transparency'] is not None:
            if self.mode in ('L', 'RGB') and mode == 'RGBA':
                # Use transparent conversion to promote from transparent
                # color to an alpha channel.
                return self._new(self.im.convert_transparent(
                    mode, self.info['transparency']))
            elif self.mode in ('L', 'RGB', 'P') and mode in ('L', 'RGB', 'P'):
                t = self.info['transparency']
                if isinstance(t, bytes):
                    # Dragons. This can't be represented by a single color
                    warnings.warn('Palette images with Transparency  ' +
                                  ' expressed in bytes should be converted ' +
                                  'to RGBA images')
                    delete_trns = True
                else:
                    # get the new transparency color.
                    # use existing conversions
                    trns_im = Image()._new(core.new(self.mode, (1, 1)))
                    if self.mode == 'P':
                        trns_im.putpalette(self.palette)
                        if type(t) == tuple:
                            try:
                                t = trns_im.palette.getcolor(t)
                            except:
                                raise ValueError("Couldn't allocate a palette "+
                                                 "color for transparency")
                    trns_im.putpixel((0, 0), t)

                    if mode in ('L', 'RGB'):
                        trns_im = trns_im.convert(mode)
                    else:
                        # can't just retrieve the palette number, got to do it
                        # after quantization.
                        trns_im = trns_im.convert('RGB')
                    trns = trns_im.getpixel((0, 0))

            elif self.mode == 'P' and mode == 'RGBA':
                t = self.info['transparency']
                delete_trns = True

                if isinstance(t, bytes):
                    self.im.putpalettealphas(t)
                elif isinstance(t, int):
                    self.im.putpalettealpha(t, 0)
                else:
                    raise ValueError("Transparency for P mode should" +
                                     " be bytes or int")

        if mode == "P" and palette == ADAPTIVE:
            im = self.im.quantize(colors)
            new = self._new(im)
            from homework import Sjn_palette
            new.palette = ImagePalette.raw("RGB", new.im.getpalette("RGB"))
            if delete_trns:
                # This could possibly happen if we requantize to fewer colors.
                # The transparency would be totally off in that case.
                del(new.info['transparency'])
            if trns is not None:
                try:
                    new.info['transparency'] = new.palette.getcolor(trns)
                except:
                    # if we can't make a transparent color, don't leave the old
                    # transparency hanging around to mess us up.
                    del(new.info['transparency'])
                    warnings.warn("Couldn't allocate palette entry " +
                                  "for transparency")
            return new

        # colorspace conversion
        if dither is None:
            dither = FLOYDSTEINBERG

        try:
            im = self.im.convert(mode, dither)
        except ValueError:
            try:
                # normalize source image and try again
                im = self.im.convert(getmodebase(self.mode))
                im = im.convert(mode, dither)
            except KeyError:
                raise ValueError("illegal conversion")

        new_im = self._new(im)
        if delete_trns:
            # crash fail if we leave a bytes transparency in an rgb/l mode.
            del(new_im.info['transparency'])
        if trns is not None:
            if new_im.mode == 'P':
                try:
                    new_im.info['transparency'] = new_im.palette.getcolor(trns)
                except:
                    del(new_im.info['transparency'])
                    warnings.warn("Couldn't allocate palette entry " +
                                  "for transparency")
            else:
                new_im.info['transparency'] = trns
        return new_im


    def quantize(self, colors=256, method=None, kmeans=0, palette=None):
        """
        Convert the image to 'P' mode with the specified number
        of colors.

        :param colors: The desired number of colors, <= 256
        :param method: 0 = median cut
                       1 = maximum coverage
                       2 = fast octree
        :param kmeans: Integer
        :param palette: Quantize to the ImagingPalette
        :returns: A new image

        """
    
        self.load()

        if method is None:
            # defaults:
            method = 0
            if self.mode == 'RGBA':
                method = 2

        if self.mode == 'RGBA' and method != 2:
            # Caller specified an invalid mode.
            raise ValueError('Fast Octree (method == 2) is the ' +
                             ' only valid method for quantizing RGBA images')

        if palette:
            # use palette from reference image
            palette.load()
            if palette.mode != "P":
                raise ValueError("bad mode for palette image")
            if self.mode != "RGB" and self.mode != "L":
                raise ValueError(
                    "only RGB or L mode images can be quantized to a palette"
                    )
            im = self.im.convert("P", 1, palette.im)
            return self._makeself(im)

        im = self.im.quantize(colors, method, kmeans)
        return self._new(im) 

    def copy(self):
        """
        Copies this image. Use this method if you wish to paste things
        into an image, but still retain the original.

        :rtype: Image.Image
        :returns: An Image.Image object.
        """
        self.load()
        im = self.im.copy()
        return self._new(im) 

    __copy__ = copy



    def getpalette(self):
        """
        Returns the image palette as a list.

        :returns: A list of color values [r, g, b, ...], or None if the
           image has no palette.
        """

        self.load()
        try:
            if bytes is str:
                return [i8(c) for c in self.im.getpalette()]
            else:
                return list(self.im.getpalette())
        except ValueError:
            return None  # no palette

    def getpixel(self, xy):
        """
        Returns the pixel value at a given position.

        :param xy: The coordinate, given as (x, y).
        :returns: The pixel value.  If the image is a multi-layer image,
           this method returns a tuple.
        """

        self.load()
        if self.pyaccess:
            return self.pyaccess.getpixel(xy)
        return self.im.getpixel(xy)

    def putpalette(self, data, rawmode="RGB"):
        """
        Attaches a palette to this image.  The image must be a "P" or
        "L" image, and the palette sequence must contain 768 integer
        values, where each group of three values represent the red,
        green, and blue values for the corresponding pixel
        index. Instead of an integer sequence, you can use an 8-bit
        string.

        :param data: A palette sequence (either a list or a string).
        """
        from homework import Sjn_palette

        if self.mode not in ("L", "P"):
            raise ValueError("illegal image mode")
        self.load()
        if isinstance(data, ImagePalette.ImagePalette):
            palette = ImagePalette.raw(data.rawmode, data.palette)
        else:
            if not isinstance(data, bytes):
                if bytes is str:
                    data = "".join(chr(x) for x in data)
                else:
                    data = bytes(data)
            palette = ImagePalette.raw(rawmode, data)
        self.mode = "P"
        self.palette = palette
        self.palette.mode = "RGB"
        self.load()  # install new palette

    def resize(self, size, resample=NEAREST):
        """
        Returns a resized copy of this image.

        :param size: The requested size in pixels, as a 2-tuple:
           (width, height).
        :param resample: An optional resampling filter.  This can be
           one of :py:attr:`PIL.Image.NEAREST` (use nearest neighbour),
           Image.BILINEAR (linear interpolation),
           Image.BICUBIC (cubic spline interpolation), or
           Image.LANCZOS (a high-quality downsampling filter).
           If omitted, or if the image has mode "1" or "P"
        """

        if resample not in (NEAREST, BILINEAR, BICUBIC, LANCZOS):
            raise ValueError("unknown resampling filter")

        self.load()

        size = tuple(size)
        if self.size == size:
            return self._new(self.im)

        if self.mode in ("1", "P"):
            resample = NEAREST

        if self.mode == 'RGBA':
            return self.convert('RGBa').resize(size, resample).convert('RGBA')

        return self._new(self.im.resize(size, resample))




    def save(self, fp, format=None, **params):
        """
        Saves this image under the given filename.  If no format is
        specified, the format to use is determined from the filename
        extension, if possible.

        You can use a file object instead of a filename. In this case,
        you must always specify the format. The file object must
        implement the seek,tell, and write
        methods, and be opened in binary mode.

        :param fp: A filename (string), pathlib.Path object or file object.
        :param format: Optional format override.  If omitted, the
           format to use is determined from the filename extension.
           If a file object was used instead of a filename, this
           parameter should always be used.
        :param options: Extra parameters to the image writer.
        :returns: None
        :exception KeyError: If the output format could not be determined
           from the file name.  Use the format option to solve this.
        :exception IOError: If the file could not be written.  The file
           may have been created, and may contain partial data.
        """

        filename = ""
        open_fp = False
        if isPath(fp):
            filename = fp
            open_fp = True
        elif sys.version_info >= (3, 4):
            from pathlib import Path
            if isinstance(fp, Path):
                filename = str(fp)
                open_fp = True
        elif hasattr(fp, "name") and isPath(fp.name):
            # only set the name for metadata purposes
            filename = fp.name

        # may mutate self!
        self.load()

        save_all = False
        if 'save_all' in params:
            save_all = params['save_all']
            del params['save_all']
        self.encoderinfo = params
        self.encoderconfig = ()

        preinit()

        ext = os.path.splitext(filename)[1].lower()

        if not format:
            if ext not in EXTENSION:
                init()
            format = EXTENSION[ext]

        if format.upper() not in SAVE:
            init()
        if save_all:
            save_handler = SAVE_ALL[format.upper()]
        else:
            save_handler = SAVE[format.upper()]

        if open_fp:
            fp = builtins.open(filename, "wb")

        try:
            save_handler(self, fp, filename)
        finally:
            # do what we can to clean up
            if open_fp:
                fp.close()



    def show(self, title=None, command=None):

        _show(self, title=title, command=command)


    


def new(mode, size, color=0):
    """
    Creates a new image with the given mode and size.

    :param mode: The mode to use for the new image. 
    :param size: A 2-tuple, containing (width, height) in pixels.
    :param color: What color to use for the image.  Default is black.
       If given, this should be a single integer or floating point value
       for single-band modes, and a tuple for multi-band modes (one value
       per band).  When creating RGB images, you can also use color
       strings as supported by the ImageColor module.  If the color is
       None, the image is not initialised.
    :returns: An Image.Image object.
    """

    if color is None:
        # don't initialize
        return Image()._new(core.new(mode, size))

    if isStringType(color):
        # css3-style specifier

        from homework import Sjn_palette
        color = Sjn_palette.getcolor(color, mode)

    return Image()._new(core.fill(mode, size, color))    

def getmodebase(mode):
    return getmode(mode).basemode

    
def open(fp, mode="r"):
    """
    Opens and identifies the given image file.

    This is a lazy operation; this function identifies the file, but
    the file remains open and the actual image data is not read from
    the file until you try to process the data (or call the

    :param fp: A filename (string), pathlib.Path object or a file object.
    :param mode: The mode.  If given, this argument must be "r".
    :returns:Image object.
    :exception IOError: If the file cannot be found, or the image cannot be
       opened and identified.
    """

    if mode != "r":
        raise ValueError("bad mode %r" % mode)

    filename = ""
    if isPath(fp):
        filename = fp
    elif sys.version_info >= (3, 4):
        from pathlib import Path
        if isinstance(fp, Path):
            filename = str(fp.resolve())
    if filename:
        fp = builtins.open(filename, "rb")

    try:
        fp.seek(0)
    except (AttributeError, io.UnsupportedOperation):
        fp = io.BytesIO(fp.read())

    prefix = fp.read(16)

    preinit()

def _show(image, **options):
    _showxv(image, **options)


def _showxv(image, title=None, **options):
    from PIL import ImageShow
    ImageShow.show(image, title, **options)    

def getmode(mode):
    if not _modes:
        # initialize mode cache
        # core modes
        for m, (basemode, basetype, bands) in Image._MODEINFO.items():
            _modes[m] = ModeDescriptor(m, bands, basemode, basetype)
        # extra experimental modes
        _modes["LA"] = ModeDescriptor("LA", ("L", "A"), "L", "L")
        _modes["PA"] = ModeDescriptor("PA", ("P", "A"), "RGB", "L")
        # mapping modes
        _modes["I;16"] = ModeDescriptor("I;16", "I", "L", "L")
        _modes["I;16L"] = ModeDescriptor("I;16L", "I", "L", "L")
        _modes["I;16B"] = ModeDescriptor("I;16B", "I", "L", "L")
    return _modes[mode]    


    
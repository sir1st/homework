import re
from PIL._binary import o8
from homework import Sjn


class GimpPaletteFile(object):

    rawmode = "RGB"

    def __init__(self, fp):

        self.palette = [o8(i)*3 for i in range(256)]

        if fp.readline()[:12] != b"GIMP Palette":
            raise SyntaxError("not a GIMP palette file")

        i = 0

        while i <= 255:

            s = fp.readline()

            if not s:
                break
            # skip fields and comment lines
            if re.match(b"\w+:|#", s):
                continue
            if len(s) > 100:
                raise SyntaxError("bad palette file")

            v = tuple(map(int, s.split()[:3]))
            if len(v) != 3:
                raise ValueError("bad palette entry")

            if 0 <= i <= 255:
                self.palette[i] = o8(v[0]) + o8(v[1]) + o8(v[2])

            i += 1

        self.palette = b"".join(self.palette)

    def getpalette(self):

        return self.palette, self.rawmode


class PaletteFile(object):

    rawmode = "RGB"

    def __init__(self, fp):

        self.palette = [(i, i, i) for i in range(256)]

        while True:

            s = fp.readline()

            if not s:
                break
            if s[0:1] == b"#":
                continue
            if len(s) > 100:
                raise SyntaxError("bad palette file")

            v = [int(x) for x in s.split()]
            try:
                [i, r, g, b] = v
            except ValueError:
                [i, r] = v
                g = b = r

            if 0 <= i <= 255:
                self.palette[i] = o8(r) + o8(g) + o8(b)

        self.palette = b"".join(self.palette)

    def getpalette(self):

        return self.palette, self.rawmode

class ImagePalette(object):
    """
    Color palette for palette mapped images

    :param mode: The mode to use for the Palette
    :param palette: An optional palette.
    :param size: An optional palette size. If given, it cannot be equal to
        or greater than 256. Defaults to 0.
    """

    def __init__(self, mode="RGB", palette=None, size=0):
        self.mode = mode
        self.rawmode = None  # if set, palette contains raw data
        self.palette = palette or list(range(256))*len(self.mode)
        self.colors = {}
        self.dirty = None
        if ((size == 0 and len(self.mode)*256 != len(self.palette)) or
                (size != 0 and size != len(self.palette))):
            raise ValueError("wrong palette size")

    def copy(self):
        new = ImagePalette()

        new.mode = self.mode
        new.rawmode = self.rawmode
        if self.palette is not None:
            new.palette = self.palette[:]
        new.colors = self.colors.copy()
        new.dirty = self.dirty

        return new

    def getdata(self):
        """
        Get palette contents in format suitable 

        """
        if self.rawmode:
            return self.rawmode, self.palette
        return self.mode + ";L", self.tobytes()

    def tobytes(self):
        """
	Convert palette to bytes.

        """
        if self.rawmode:
            raise ValueError("palette contains raw palette data")
        if isinstance(self.palette, bytes):
            return self.palette
        arr = array.array("B", self.palette)
        if hasattr(arr, 'tobytes'):
            return arr.tobytes()
        return arr.tostring()

    # Declare tostring as an alias for tobytes
    tostring = tobytes

    def getcolor(self, color):
        """
	Given an rgb tuple, allocate palette entry.

        """
        if self.rawmode:
            raise ValueError("palette contains raw palette data")
        if isinstance(color, tuple):
            try:
                return self.colors[color]
            except KeyError:
                # allocate new color slot
                if isinstance(self.palette, bytes):
                    self.palette = [int(x) for x in self.palette]
                index = len(self.colors)
                if index >= 256:
                    raise ValueError("cannot allocate more than 256 colors")
                self.colors[color] = index
                self.palette[index] = color[0]
                self.palette[index+256] = color[1]
                self.palette[index+512] = color[2]
                self.dirty = 1
                return index
        else:
            raise ValueError("unknown color specifier: %r" % color)


def raw(rawmode, data):
    palette = ImagePalette()
    palette.rawmode = rawmode
    palette.palette = data
    palette.dirty = 1
    return palette

def load(filename):

    # FIXME: supports GIMP gradients only

    fp = open(filename, "rb")

    lut = None

    if not lut:
        try:
            fp.seek(0)
            p = GimpPaletteFile(fp)
            lut = p.getpalette()
        except (SyntaxError, ValueError):
            # import traceback
            # traceback.print_exc()
            pass

    if not lut:
        try:
            fp.seek(0)
            p = GimpGradientFile(fp)
            lut = p.getpalette()
        except (SyntaxError, ValueError):
            # import traceback
            # traceback.print_exc()
            pass

    if not lut:
        try:
            fp.seek(0)
            p = PaletteFile(fp)
            lut = p.getpalette()
        except (SyntaxError, ValueError):
            # import traceback
            # traceback.print_exc()
            pass

    if not lut:
        raise IOError("cannot load palette")

    return lut  # data, rawmode

def getrgb(color):
    """
     Convert a color string to an RGB tuple. 
    :param color: A color string
    :return: (red, green, blue[, alpha])
    """
    try:
        rgb = colormap[color]
    except KeyError:
        try:
            # fall back on case-insensitive lookup
            rgb = colormap[color.lower()]
        except KeyError:
            rgb = None
    # found color in cache
    if rgb:
        if isinstance(rgb, tuple):
            return rgb
        colormap[color] = rgb = getrgb(rgb)
        return rgb
    # check for known string formats
    m = re.match("#\w\w\w$", color)
    if m:
        return (
            int(color[1]*2, 16),
            int(color[2]*2, 16),
            int(color[3]*2, 16)
            )
    m = re.match("#\w\w\w\w\w\w$", color)
    if m:
        return (
            int(color[1:3], 16),
            int(color[3:5], 16),
            int(color[5:7], 16)
            )
    m = re.match("rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$", color)
    if m:
        return (
            int(m.group(1)),
            int(m.group(2)),
            int(m.group(3))
            )
    m = re.match("rgb\(\s*(\d+)%\s*,\s*(\d+)%\s*,\s*(\d+)%\s*\)$", color)
    if m:
        return (
            int((int(m.group(1)) * 255) / 100.0 + 0.5),
            int((int(m.group(2)) * 255) / 100.0 + 0.5),
            int((int(m.group(3)) * 255) / 100.0 + 0.5)
            )
    m = re.match("hsl\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%\s*\)$", color)
    if m:
        from colorsys import hls_to_rgb
        rgb = hls_to_rgb(
            float(m.group(1)) / 360.0,
            float(m.group(3)) / 100.0,
            float(m.group(2)) / 100.0,
            )
        return (
            int(rgb[0] * 255 + 0.5),
            int(rgb[1] * 255 + 0.5),
            int(rgb[2] * 255 + 0.5)
            )
    m = re.match("rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$",
                 color)
    if m:
        return (
            int(m.group(1)),
            int(m.group(2)),
            int(m.group(3)),
            int(m.group(4))
            )
    raise ValueError("unknown color specifier: %r" % color)


def getcolor(color, mode):
   
    # same as getrgb, but converts the result to the given mode
    color, alpha = getrgb(color), 255
    if len(color) == 4:
        color, alpha = color[0:3], color[3]

    if Sjn.getmodebase(mode) == "L":
        r, g, b = color
        color = (r*299 + g*587 + b*114)//1000
        if mode[-1] == 'A':
            return (color, alpha)
    else:
        if mode[-1] == 'A':
            return color + (alpha,)
    return color

colormap = {
    # X11 colour table (from "CSS3 module: Color working draft"), with
    # gray/grey spelling issues fixed.  This is a superset of HTML 4.0
    # colour names used in CSS 1.
    "aliceblue": "#f0f8ff",
    "antiquewhite": "#faebd7",
    "aqua": "#00ffff",
    "aquamarine": "#7fffd4",
    "azure": "#f0ffff",
    "beige": "#f5f5dc",
    "bisque": "#ffe4c4",
    "black": "#000000",
    "blanchedalmond": "#ffebcd",
    "blue": "#0000ff",
    "blueviolet": "#8a2be2",
    "brown": "#a52a2a",
    "burlywood": "#deb887",
    "cadetblue": "#5f9ea0",
    "chartreuse": "#7fff00",
    "chocolate": "#d2691e",
    "coral": "#ff7f50",
    "cornflowerblue": "#6495ed",
    "cornsilk": "#fff8dc",
    "crimson": "#dc143c",
    "cyan": "#00ffff",
    "darkblue": "#00008b",
    "darkcyan": "#008b8b",
    "darkgoldenrod": "#b8860b",
    "darkgray": "#a9a9a9",
    "darkgrey": "#a9a9a9",
    "darkgreen": "#006400",
    "darkkhaki": "#bdb76b",
    "darkmagenta": "#8b008b",
    "darkolivegreen": "#556b2f",
    "darkorange": "#ff8c00",
    "darkorchid": "#9932cc",
    "darkred": "#8b0000",
    "darksalmon": "#e9967a",
    "darkseagreen": "#8fbc8f",
    "darkslateblue": "#483d8b",
    "darkslategray": "#2f4f4f",
    "darkslategrey": "#2f4f4f",
    "darkturquoise": "#00ced1",
    "darkviolet": "#9400d3",
    "deeppink": "#ff1493",
    "deepskyblue": "#00bfff",
    "dimgray": "#696969",
    "dimgrey": "#696969",
    "dodgerblue": "#1e90ff",
    "firebrick": "#b22222",
    "floralwhite": "#fffaf0",
    "forestgreen": "#228b22",
    "fuchsia": "#ff00ff",
    "gainsboro": "#dcdcdc",
    "ghostwhite": "#f8f8ff",
    "gold": "#ffd700",
    "goldenrod": "#daa520",
    "gray": "#808080",
    "grey": "#808080",
    "green": "#008000",
    "greenyellow": "#adff2f",
    "honeydew": "#f0fff0",
    "hotpink": "#ff69b4",
    "indianred": "#cd5c5c",
    "indigo": "#4b0082",
    "ivory": "#fffff0",
    "khaki": "#f0e68c",
    "lavender": "#e6e6fa",
    "lavenderblush": "#fff0f5",
    "lawngreen": "#7cfc00",
    "lemonchiffon": "#fffacd",
    "lightblue": "#add8e6",
    "lightcoral": "#f08080",
    "lightcyan": "#e0ffff",
    "lightgoldenrodyellow": "#fafad2",
    "lightgreen": "#90ee90",
    "lightgray": "#d3d3d3",
    "lightgrey": "#d3d3d3",
    "lightpink": "#ffb6c1",
    "lightsalmon": "#ffa07a",
    "lightseagreen": "#20b2aa",
    "lightskyblue": "#87cefa",
    "lightslategray": "#778899",
    "lightslategrey": "#778899",
    "lightsteelblue": "#b0c4de",
    "lightyellow": "#ffffe0",
    "lime": "#00ff00",
    "limegreen": "#32cd32",
    "linen": "#faf0e6",
    "magenta": "#ff00ff",
    "maroon": "#800000",
    "mediumaquamarine": "#66cdaa",
    "mediumblue": "#0000cd",
    "mediumorchid": "#ba55d3",
    "mediumpurple": "#9370db",
    "mediumseagreen": "#3cb371",
    "mediumslateblue": "#7b68ee",
    "mediumspringgreen": "#00fa9a",
    "mediumturquoise": "#48d1cc",
    "mediumvioletred": "#c71585",
    "midnightblue": "#191970",
    "mintcream": "#f5fffa",
    "mistyrose": "#ffe4e1",
    "moccasin": "#ffe4b5",
    "navajowhite": "#ffdead",
    "navy": "#000080",
    "oldlace": "#fdf5e6",
    "olive": "#808000",
    "olivedrab": "#6b8e23",
    "orange": "#ffa500",
    "orangered": "#ff4500",
    "orchid": "#da70d6",
    "palegoldenrod": "#eee8aa",
    "palegreen": "#98fb98",
    "paleturquoise": "#afeeee",
    "palevioletred": "#db7093",
    "papayawhip": "#ffefd5",
    "peachpuff": "#ffdab9",
    "peru": "#cd853f",
    "pink": "#ffc0cb",
    "plum": "#dda0dd",
    "powderblue": "#b0e0e6",
    "purple": "#800080",
    "red": "#ff0000",
    "rosybrown": "#bc8f8f",
    "royalblue": "#4169e1",
    "saddlebrown": "#8b4513",
    "salmon": "#fa8072",
    "sandybrown": "#f4a460",
    "seagreen": "#2e8b57",
    "seashell": "#fff5ee",
    "sienna": "#a0522d",
    "silver": "#c0c0c0",
    "skyblue": "#87ceeb",
    "slateblue": "#6a5acd",
    "slategray": "#708090",
    "slategrey": "#708090",
    "snow": "#fffafa",
    "springgreen": "#00ff7f",
    "steelblue": "#4682b4",
    "tan": "#d2b48c",
    "teal": "#008080",
    "thistle": "#d8bfd8",
    "tomato": "#ff6347",
    "turquoise": "#40e0d0",
    "violet": "#ee82ee",
    "wheat": "#f5deb3",
    "white": "#ffffff",
    "whitesmoke": "#f5f5f5",
    "yellow": "#ffff00",
    "yellowgreen": "#9acd32",


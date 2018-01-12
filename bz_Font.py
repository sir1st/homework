from ._util import isDirectory, isPath
import os
import sys
class FreeTypeFont(object):
    "FreeType font wrapper (requires _imagingft service)"

    def __init__(self, font=None, size=10, index=0, encoding="",
                 layout_engine=None):
        # FIXME: use service provider instead

        self.path = font
        self.size = size
        self.index = index
        self.encoding = encoding

        if layout_engine not in (LAYOUT_BASIC, LAYOUT_RAQM):
            layout_engine = LAYOUT_BASIC
            if core.HAVE_RAQM:
                layout_engine = LAYOUT_RAQM
        if layout_engine == LAYOUT_RAQM and not core.HAVE_RAQM:
            layout_engine = LAYOUT_BASIC

        self.layout_engine = layout_engine

        if isPath(font):
            self.font = core.getfont(font, size, index, encoding, layout_engine=layout_engine)
        else:
            self.font_bytes = font.read()
            self.font = core.getfont(
                "", size, index, encoding, self.font_bytes, layout_engine)

    def getname(self):
        return self.font.family, self.font.style

    def getmetrics(self):
        return self.font.ascent, self.font.descent

    def getsize(self, text, direction=None, features=None):
        size, offset = self.font.getsize(text, direction, features)
        return (size[0] + offset[0], size[1] + offset[1])

    def getoffset(self, text):
        return self.font.getsize(text)[1]

    def getmask(self, text, mode="", direction=None, features=None):
        return self.getmask2(text, mode, direction=direction, features=features)[0]

    def getmask2(self, text, mode="", fill=Image.core.fill, direction=None, features=None, *args, **kwargs):
        size, offset = self.font.getsize(text, direction, features)
        im = fill("L", size, 0)
        self.font.render(text, im.id, mode == "1", direction, features)
        return im, offset

    def font_variant(self, font=None, size=None, index=None, encoding=None,
                     layout_engine=None):
        """
        Create a copy of this FreeTypeFont object,
        using any specified arguments to override the settings.

        Parameters are identical to the parameters used to initialize this
        object.

        :return: A FreeTypeFont object.
        """
        return FreeTypeFont(font=self.path if font is None else font,
                            size=self.size if size is None else size,
                            index=self.index if index is None else index,
                            encoding=self.encoding if encoding is None else encoding,
                            layout_engine=self.layout_engine if layout_engine is None else layout_engine
                            )



def truetype(font=None, size=10, index=0, encoding="",
             layout_engine=None):

    try:
        return FreeTypeFont(font, size, index, encoding, layout_engine)
    except IOError:
        ttf_filename = os.path.basename(font)

        dirs = []
        if sys.platform == "win32":
            # check the windows font repository
            # NOTE: must use uppercase WINDIR, to work around bugs in
            # 1.5.2's os.environ.get()
            windir = os.environ.get("WINDIR")
            if windir:
                dirs.append(os.path.join(windir, "fonts"))
        elif sys.platform in ('linux', 'linux2'):
            lindirs = os.environ.get("XDG_DATA_DIRS", "")
            if not lindirs:
                # According to the freedesktop spec, XDG_DATA_DIRS should
                # default to /usr/share
                lindirs = '/usr/share'
            dirs += [os.path.join(lindir, "fonts")
                     for lindir in lindirs.split(":")]
        elif sys.platform == 'darwin':
            dirs += ['/Library/Fonts', '/System/Library/Fonts',
                     os.path.expanduser('~/Library/Fonts')]

        ext = os.path.splitext(ttf_filename)[1]
        first_font_with_a_different_extension = None
        for directory in dirs:
            for walkroot, walkdir, walkfilenames in os.walk(directory):
                for walkfilename in walkfilenames:
                    if ext and walkfilename == ttf_filename:
                        fontpath = os.path.join(walkroot, walkfilename)
                        return FreeTypeFont(fontpath, size, index, encoding, layout_engine)
                    elif not ext and os.path.splitext(walkfilename)[0] == ttf_filename:
                        fontpath = os.path.join(walkroot, walkfilename)
                        if os.path.splitext(fontpath)[1] == '.ttf':
                            return FreeTypeFont(fontpath, size, index, encoding, layout_engine)
                        if not ext and first_font_with_a_different_extension is None:
                            first_font_with_a_different_extension = fontpath
        if first_font_with_a_different_extension:
            return FreeTypeFont(first_font_with_a_different_extension, size,
                                index, encoding, layout_engine)
        raise


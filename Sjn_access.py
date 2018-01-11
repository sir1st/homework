class PyAccess(object):

    def __init__(self, img, readonly=False):
        vals = dict(img.im.unsafe_ptrs)
        self.readonly = readonly
        self.image8 = ffi.cast('unsigned char **', vals['image8'])
        self.image32 = ffi.cast('int **', vals['image32'])
        self.image = ffi.cast('unsigned char **', vals['image'])
        self.xsize = vals['xsize']
        self.ysize = vals['ysize']

        # Debugging is polluting test traces, only useful here
        # when hacking on PyAccess
        # logger.debug("%s", vals)
        self._post_init()

     def __setitem__(self, xy, color):
        """
        Modifies the pixel at x,y. The color is given as a single
        numerical value for single band images, and a tuple for
        multi-band images

        :param xy: The pixel coordinate, given as (x, y).
        :param value: The pixel value.
        """
        if self.readonly:
            raise ValueError('Attempt to putpixel a read only image')
        (x, y) = self.check_xy(xy)
        return self.set_pixel(x, y, color)

    def __getitem__(self, xy):
        """
        Returns the pixel at x,y. The pixel is returned as a single
        value for single band images or a tuple for multiple band
        images

        :param xy: The pixel coordinate, given as (x, y).
        :returns: a pixel value for single band images, a tuple of
          pixel values for multiband images.
        """

        (x, y) = self.check_xy(xy)
        return self.get_pixel(x, y)

    putpixel = __setitem__
    getpixel = __getitem__

mode_map = {'1': _PyAccess8,
            'L': _PyAccess8,
            'P': _PyAccess8,
            'LA': _PyAccess32_2,
            'PA': _PyAccess32_2,
            'RGB': _PyAccess32_3,
            'LAB': _PyAccess32_3,
            'HSV': _PyAccess32_3,
            'YCbCr': _PyAccess32_3,
            'RGBA': _PyAccess32_4,
            'RGBa': _PyAccess32_4,
            'RGBX': _PyAccess32_4,
            'CMYK': _PyAccess32_4,
            'F': _PyAccessF,
            'I': _PyAccessI32_N,
            }

if sys.byteorder == 'little':
    mode_map['I;16'] = _PyAccessI16_N
    mode_map['I;16L'] = _PyAccessI16_N
    mode_map['I;16B'] = _PyAccessI16_B

    mode_map['I;32L'] = _PyAccessI32_N
    mode_map['I;32B'] = _PyAccessI32_Swap
else:
    mode_map['I;16'] = _PyAccessI16_L
    mode_map['I;16L'] = _PyAccessI16_L
    mode_map['I;16B'] = _PyAccessI16_N

    mode_map['I;32L'] = _PyAccessI32_Swap
    mode_map['I;32B'] = _PyAccessI32_N


def new(img, readonly=False):
    access_type = mode_map.get(img.mode, None)
    if not access_type:
        logger.debug("PyAccess Not Implemented: %s", img.mode)
        return None
    return access_type(img, readonly)
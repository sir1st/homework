def Draw(im, mode=None):
    try:
        return im.getdraw(mode)
    except AttributeError:
        return ImageDraw(im, mode)
		
class ImageDraw(object):

    def __init__(self, im, mode=None):
        
        im.load()
        if im.readonly:
            im._copy()  # make it writeable
        blend = 0
        if mode is None:
            mode = im.mode
        if mode != im.mode:
            if mode == "RGBA" and im.mode == "RGB":
                blend = 1
            else:
                raise ValueError("mode mismatch")
        if mode == "P":
            self.palette = im.palette
        else:
            self.palette = None
        self.im = im.im
        self.draw = Image.core.draw(self.im, blend)
        self.mode = mode
        if mode in ("I", "F"):
            self.ink = self.draw.draw_ink(1, mode)
        else:
            self.ink = self.draw.draw_ink(-1, mode)
        if mode in ("1", "P", "I", "F"):
           
            self.fontmode = "1"
        else:
            self.fontmode = "L"  
        self.fill = 0
        self.font = None

def getdraw(im=None, hints=None):
    
    handler = None
    if not hints or "nicest" in hints:
        try:
            from . import _imagingagg as handler
        except ImportError:
            pass
    if handler is None:
        from . import ImageDraw2 as handler
    if im:
        im = handler.Draw(im)
    return im, handler
	

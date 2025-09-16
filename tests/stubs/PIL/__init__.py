class DummyImage:
    def __init__(self, width=100, height=100):
        self.width = width
        self.height = height
        self.mode = 'RGBA'
    @property
    def size(self):
        return (self.width, self.height)

    def convert(self, mode):
        self.mode = mode
        return self

    def resize(self, size, resample=None):
        self.width, self.height = size
        return self

    def save(self, fp, *args, **kwargs):
        if hasattr(fp, 'write'):
            fp.write(b'dummy')
        else:
            with open(fp, 'wb') as f:
                f.write(b'dummy')

    def alpha_composite(self, other):
        pass

    def paste(self, img, pos, mask=None):
        pass

class Image:
    @staticmethod
    def open(fp):
        return DummyImage()

    @staticmethod
    def new(mode, size, color=(0, 0, 0, 0)):
        return DummyImage(*size)

    Resampling = type('Resampling', (), {'LANCZOS': 0})
    Image = DummyImage

class ImageDraw:
    class Draw:
        def __init__(self, img):
            pass
        def text(self, *args, **kwargs):
            pass
        def rectangle(self, *args, **kwargs):
            pass
        def textbbox(self, xy, text, font=None):
            # return left, top, right, bottom
            return (0, 0, len(text) * 10, 10)
        def textlength(self, text, font=None):
            return len(text) * 10

    ImageDraw = Draw

class ImageFont:
    class FreeTypeFont:
        pass

    @staticmethod
    def truetype(font, size):
        return ImageFont.FreeTypeFont()

    @staticmethod
    def load_default():
        return ImageFont.FreeTypeFont()

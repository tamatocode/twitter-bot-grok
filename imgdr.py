# imghdr.py (custom shim for Python 3.13)
def what(file, h=None):
    """Minimal version of imghdr.what() for Tweepy compatibility."""
    if h is None:
        with open(file, 'rb') as f:
            h = f.read(32)

    # JPEG
    if h[6:10] in (b'JFIF', b'Exif'):
        return 'jpeg'
    # PNG
    if h[:8] == b'\211PNG\r\n\032\n':
        return 'png'
    # GIF
    if h[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'
    # BMP
    if h[:2] == b'BM':
        return 'bmp'
    # WebP
    if h[:4] == b'RIFF' and h[8:12] == b'WEBP':
        return 'webp'

    return None

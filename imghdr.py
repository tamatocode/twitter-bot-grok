def what(file, h=None):
    if h is None:
        with open(file, "rb") as f:
            h = f.read(32)
    if h[6:10] in (b"JFIF", b"Exif"):
        return "jpeg"
    if h[:8] == b"\211PNG\r\n\032\n":
        return "png"
    if h[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if h[:2] == b"BM":
        return "bmp"
    if h[:4] == b"RIFF" and h[8:12] == b"WEBP":
        return "webp"
    return None

"""Bounded, in-memory image / ZIP handling; archive paths are never extracted."""
import io
import warnings
import zipfile
from pathlib import PurePosixPath
from PIL import Image, ImageOps

MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_UPLOAD_BYTES = 100 * 1024 * 1024
MAX_TOTAL_BYTES = 200 * 1024 * 1024
MAX_IMAGES = 60
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
Image.MAX_IMAGE_PIXELS = 25_000_000


def decode_image(data):
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError('Image exceeds 20 MiB.')
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(data)) as original:
            original.load()
            image = ImageOps.exif_transpose(original).convert('RGB')
    image.thumbnail((1024, 1024))
    return image


def zip_images(data):
    """Return (filename, bytes) pairs after validating all member sizes first."""
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError('ZIP exceeds 100 MiB.')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = []
        total = 0
        for info in archive.infolist():
            path = PurePosixPath(info.filename)
            if info.is_dir() or '__MACOSX' in path.parts or path.name.startswith('.'):
                continue
            if path.suffix.lower() not in EXTENSIONS:
                continue
            if path.is_absolute() or '..' in path.parts or '\\' in info.filename:
                raise ValueError('ZIP contains an unsafe image path.')
            if info.flag_bits & 1:
                raise ValueError('Encrypted ZIP members are unsupported.')
            if info.file_size > MAX_IMAGE_BYTES:
                raise ValueError(f'{path.name}: exceeds 20 MiB.')
            if info.file_size / max(info.compress_size, 1) > 200:
                raise ValueError('ZIP compression ratio is excessive.')
            total += info.file_size
            entries.append(info)
        if not entries:
            raise ValueError('ZIP contains no JPG, PNG or WebP images.')
        if len(entries) > MAX_IMAGES or total > MAX_TOTAL_BYTES:
            raise ValueError('ZIP limit: 60 images and 200 MiB total uncompressed.')
        result = []
        for info in entries:
            with archive.open(info) as member:
                payload = member.read(MAX_IMAGE_BYTES + 1)
            if len(payload) > MAX_IMAGE_BYTES:
                raise ValueError('Expanded image exceeds the limit.')
            result.append((info.filename, payload))
        return result

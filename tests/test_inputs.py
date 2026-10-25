import io
import unittest
import zipfile
from PIL import Image
from caption_app.image_inputs import decode_image, zip_images


def image_bytes():
    buffer = io.BytesIO()
    Image.new('RGB', (32, 24), 'blue').save(buffer, format='PNG')
    return buffer.getvalue()


def archive_bytes(entries):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        for name, data in entries:
            archive.writestr(name, data)
    return buffer.getvalue()


class UploadTests(unittest.TestCase):
    def test_valid_image_preserves_size_and_rgb(self):
        image = decode_image(image_bytes())
        self.assertEqual(image.size, (32, 24))
        self.assertEqual(image.mode, 'RGB')

    def test_corrupt_image_is_rejected(self):
        with self.assertRaises(Exception):
            decode_image(b'broken image')

    def test_zip_ignores_mac_metadata_and_non_images(self):
        result = zip_images(archive_bytes([('photo.png', image_bytes()),
            ('__MACOSX/._photo.png', b'ignored'), ('notes.txt', b'ignored')]))
        self.assertEqual([name for name, _ in result], ['photo.png'])

    def test_unsafe_member_is_rejected(self):
        with self.assertRaises(ValueError):
            zip_images(archive_bytes([('../outside.png', image_bytes())]))

    def test_empty_zip_is_rejected(self):
        with self.assertRaises(ValueError):
            zip_images(archive_bytes([('notes.txt', b'not an image')]))

    def test_excessive_count_is_rejected(self):
        with self.assertRaises(ValueError):
            zip_images(archive_bytes([(f'{i}.png', image_bytes()) for i in range(61)]))


if __name__ == '__main__':
    unittest.main()

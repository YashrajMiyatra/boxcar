import os
import shutil
import tempfile
import unittest
from boxcar.storage import ImageStore


class TestImageStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store = ImageStore(base_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_image_lifecycle(self):
        rootfs = self.store.get_rootfs("test_image", "latest")
        os.makedirs(rootfs, exist_ok=True)
        with open(os.path.join(rootfs, "test.txt"), "w") as f:
            f.write("hello container")

        self.store.save_metadata("test_image", "latest", ["sha256:1234567890ab"])
        self.assertTrue(self.store.image_exists("test_image", "latest"))

        images = self.store.list_images()
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]["image"], "test_image")

        deleted = self.store.delete_image("test_image", "latest")
        self.assertTrue(deleted)
        self.assertFalse(self.store.image_exists("test_image", "latest"))


if __name__ == "__main__":
    unittest.main()

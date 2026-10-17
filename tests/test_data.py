import tempfile
import unittest
from pathlib import Path
from PIL import Image
import numpy as np
from cracklens.data.prepare import import_paired_dataset

class DatasetImportTests(unittest.TestCase):
    def test_deepcrack_style_layout_is_paired_and_split(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "source"
            for folder in ("train_img", "train_lab", "test_img", "test_lab"):
                (root / folder).mkdir(parents=True)
            for index in range(6):
                split = "train" if index < 4 else "test"
                image = np.full((12, 16, 3), index * 20, dtype=np.uint8)
                mask = np.zeros((12, 16), dtype=np.uint8)
                mask[2:8, index:index + 2] = 255
                Image.fromarray(image).save(root / f"{split}_img" / f"frame_{index}.jpg")
                Image.fromarray(mask).save(root / f"{split}_lab" / f"frame_{index}.png")
            output = Path(temp) / "processed"
            summary = import_paired_dataset(root, output, seed=7, source="test")
            self.assertIsNotNone(summary)
            self.assertEqual(summary.count, 6)
            self.assertEqual(summary.train + summary.val + summary.test, 6)
            for split in ("train", "val", "test"):
                image_files = list((output / "images" / split).glob("*.png"))
                mask_files = list((output / "masks" / split).glob("*.png"))
                self.assertEqual(len(image_files), len(mask_files))
                self.assertTrue(all(path.name in {item.name for item in mask_files} for path in image_files))
            self.assertEqual(summary.source, "test")

if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import unittest

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


class BrandAssetTests(unittest.TestCase):
    def assert_image(self, relative_path: str, size: tuple[int, int]) -> None:
        path = ROOT / relative_path
        self.assertTrue(path.is_file(), f"Missing asset: {relative_path}")
        with Image.open(path) as image:
            self.assertEqual(image.size, size)
            self.assertEqual(image.format, "PNG")

    def test_source_master(self) -> None:
        self.assert_image(
            "assets/source/downatthebottomofthemolehole_banner_20.png",
            (1536, 1024),
        )

    def test_github_banner(self) -> None:
        self.assert_image("assets/banners/rolfmoleman-github.png", (1983, 793))

    def test_justgiving_cover(self) -> None:
        relative_path = "assets/banners/rolfmoleman-justgiving-mind.png"
        self.assert_image(relative_path, (1000, 563))
        self.assertLessEqual((ROOT / relative_path).stat().st_size, 4 * 1024 * 1024)

    def test_avatar_master(self) -> None:
        self.assert_image("assets/avatars/rolfmoleman-avatar.png", (1024, 1024))

    def test_personal_mark(self) -> None:
        self.assert_image("assets/logos/rolfmoleman-mark.png", (1024, 1024))


if __name__ == "__main__":
    unittest.main()

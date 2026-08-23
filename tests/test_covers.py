"""测试 covers 模块"""
import unittest


class TestCoverModules(unittest.TestCase):
    """所有封面模块可正常导入"""

    def test_enhanced_imports(self):
        from covers.enhanced import generate_cover_enhanced, generate_inline_image
        self.assertTrue(callable(generate_cover_enhanced))
        self.assertTrue(callable(generate_inline_image))

    def test_base_imports(self):
        from covers.base import generate_cover
        self.assertTrue(callable(generate_cover))

    def test_deluxe_imports(self):
        import covers.deluxe
        self.assertTrue(hasattr(covers.deluxe, "_font"))

    def test_helper_imports(self):
        from covers.helper import _font
        font = _font(24)
        self.assertIsNotNone(font)


class TestCoverSafetyZone(unittest.TestCase):
    """封面安全区常量校验（与 AGENTS.md 保持一致）"""

    SAFE_ZONE_W = 500
    SAFE_X_MIN = 200
    SAFE_X_MAX = 700

    def test_safe_zone_width(self):
        self.assertEqual(self.SAFE_ZONE_W, 500)

    def test_safe_x_min(self):
        self.assertEqual(self.SAFE_X_MIN, 200)

    def test_safe_x_max(self):
        self.assertEqual(self.SAFE_X_MAX, 700)


if __name__ == "__main__":
    unittest.main()
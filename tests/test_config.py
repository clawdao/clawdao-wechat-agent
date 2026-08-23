"""测试 config 模块"""
import unittest


class TestConfig(unittest.TestCase):
    """config 加载与各段读取测试"""

    def test_config_loads(self):
        from config import load_config
        cfg = load_config()
        self.assertIsInstance(cfg, dict)

    def test_get_api_config(self):
        from config import get_api_config
        cfg = get_api_config()
        self.assertIsInstance(cfg, dict)

    def test_get_wechat_config(self):
        from config import get_wechat_config
        cfg = get_wechat_config()
        self.assertIsInstance(cfg, dict)

    def test_get_cover_config(self):
        from config import get_cover_config
        cfg = get_cover_config()
        self.assertIsInstance(cfg, dict)

    def test_get_seedream_config(self):
        from config import get_seedream_config
        cfg = get_seedream_config()
        self.assertIsInstance(cfg, dict)

    def test_get_output_config(self):
        from config import get_output_config
        cfg = get_output_config()
        self.assertIsInstance(cfg, dict)


if __name__ == "__main__":
    unittest.main()
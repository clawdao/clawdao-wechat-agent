"""测试 core.publisher 模块"""
import unittest


class TestWeChatPublisher(unittest.TestCase):
    """WeChatPublisher 类测试"""

    def test_class_exists(self):
        from core.publisher import WeChatPublisher
        self.assertTrue(hasattr(WeChatPublisher, "__init__"))


if __name__ == "__main__":
    unittest.main()
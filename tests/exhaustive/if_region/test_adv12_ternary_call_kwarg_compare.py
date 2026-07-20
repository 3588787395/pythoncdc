import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv12TernaryCallKwargCompare(ExhaustiveTestCase):
    # if 条件中三元作关键字参数: if f(x=a if c else b) > 0
    # 字节码含 KW_NAMES（栈模拟需识别为 keyword arg）。
    SOURCE_CODE = """if f(x=a if c else b) > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

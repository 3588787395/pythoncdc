import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv12TernaryMethodCall(ExhaustiveTestCase):
    # if 条件中三元表达式作方法调用的 receiver: if (a if c else b).m() > 0
    # 字节码含 LOAD_METHOD（栈模拟需识别为 Attribute）。
    SOURCE_CODE = """if (a if c else b).m() > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv12TernaryCallArgBinaryOp(ExhaustiveTestCase):
    # if 条件中三元 call 参数参与二元运算: if f(a if c else b) + 1 > 0
    # 字节码含 BINARY_OP（栈模拟需将 arg int 映射为操作符字符串）。
    SOURCE_CODE = """if f(a if c else b) + 1 > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

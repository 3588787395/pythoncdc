import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv12TernaryCallArgUnaryOp(ExhaustiveTestCase):
    # if 条件中三元 call 参数取负: if -f(a if c else b) > 0
    # 字节码含 UNARY_NEGATIVE（栈模拟需识别为 UnaryOpUSub）。
    SOURCE_CODE = """if -f(a if c else b) > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv14BoolopSingleCompare(ExhaustiveTestCase):
    # boolop 结果与单个值比较：
    # if (a or b) == c:
    #     pass
    # 字节码 LOAD_NAME a / LOAD_NAME b / JUMP_IF_TRUE_OR_POP
    # / LOAD_NAME c / COMPARE_OP == / POP_JUMP_IF_FALSE。
    # or 的结果作为 == 的左操作数，反编译器需正确生成括号。
    SOURCE_CODE = """if (a or b) == c:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

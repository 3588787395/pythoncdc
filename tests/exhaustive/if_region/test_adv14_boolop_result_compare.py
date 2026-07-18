import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv14BoolopResultCompare(ExhaustiveTestCase):
    # boolop 结果比较：
    # if (a and b) == (c and d):
    #     pass
    # 字节码 LOAD_NAME a / LOAD_NAME b / JUMP_IF_FALSE_OR_POP
    # / LOAD_NAME c / LOAD_NAME d / JUMP_IF_FALSE_OR_POP
    # / COMPARE_OP == / POP_JUMP_IF_FALSE。
    # 实际上左右两个 and 的结果会先求值再 == 比较，括号分组关键。
    SOURCE_CODE = """if (a and b) == (c and d):
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

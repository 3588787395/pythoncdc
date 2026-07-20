import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv14NestedNotBoolop(ExhaustiveTestCase):
    # 嵌套 not：
    # if not (a or b) and not (c or d):
    #     pass
    # 字节码 LOAD_NAME a / LOAD_NAME b / JUMP_IF_TRUE_OR_POP
    # / LOAD_NAME a / LOAD_NAME b / UNARY_NOT...
    # 实际为 LOAD_NAME a / LOAD_NAME b / JUMP_IF_TRUE_OR_POP / POP_JUMP...
    # 两个 not(or(...)) 由 and 连接，UNARY_NOT 作用于 boolop 结果。
    SOURCE_CODE = """if not (a or b) and not (c or d):
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

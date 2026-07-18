import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv13TernaryBinaryOpCond(ExhaustiveTestCase):
    # if 条件中三元表达式作 BINARY_OP 左操作数 + 比较：
    # if (a if c else b) + 1 > 0:
    #     pass
    # 字节码 LOAD_NAME a / LOAD_NAME b / <三元跳转> / LOAD_CONST 1 / BINARY_OP +
    # / LOAD_CONST 0 / COMPARE_OP > / POP_JUMP_IF_FALSE。
    # BINARY_OP 不在 _WRAPPING_OPS 中，三元 merge_block 后的 BINARY_OP 包裹可能失败。
    SOURCE_CODE = """if (a if c else b) + 1 > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

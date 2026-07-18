import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv13TernaryInFstringCond(ExhaustiveTestCase):
    # if 条件中 f-string 内部包含三元表达式 + 等于比较：
    # if f"{a if c else b}" == "x":
    #     pass
    # 字节码 LOAD_NAME a / LOAD_NAME b / <三元跳转> / FORMAT_VALUE 0
    # / LOAD_CONST 'x' / COMPARE_OP == / POP_JUMP_IF_FALSE。
    # 三元表达式在 FORMAT_VALUE 之前求值，FORMAT_VALUE 不在 _WRAPPING_OPS 中，
    # 可能导致三元与 f-string 包裹的归约失败。
    SOURCE_CODE = '''if f"{a if c else b}" == "x":
    pass'''
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

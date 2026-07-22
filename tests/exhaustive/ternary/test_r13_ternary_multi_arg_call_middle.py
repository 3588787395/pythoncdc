import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryMultiArgCallMiddle(ExhaustiveTestCase):
    """Bug R13 (new): f(0, (a if c else b), 1) — ternary as middle positional arg。

    原始:
        f(0, (a if c else b), 1)
    缺陷: ternary 作为多参数 Call 的中间位置参数。cond_block preload 含
         PUSH_NULL + LOAD_GLOBAL f + LOAD_CONST 0（前位置参数），ternary merge
         块栈输出作为中间位置参数，merge_block 之后还有 LOAD_CONST 1（后位置参数），
         然后 PRECALL + CALL 3。R2 已测 ternary_in_multi_arg_call（test_r2_ternary
         _in_multi_arg_call，2 个参数），R13 测 3 个参数且 ternary 在中间的变体。
    """
    SOURCE_CODE = """f(0, (a if c else b), 1)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

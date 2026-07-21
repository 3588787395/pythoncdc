import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryTypeThreeArgs(ExhaustiveTestCase):
    """Bug R15 (new): type('X', (a if c else b), {}) — type 三参数 ternary 作基类。

    原始:
        type('X', (a if c else b), {})
    缺陷: ternary 作为 type 三参数调用的第二位置参数（基类）。cond_block
         preload 含 PUSH_NULL + LOAD type + LOAD_CONST 'X'，ternary merge 块
         栈顶与 BUILD_MAP 0 一起 PRECALL + CALL 3 消费。
    """
    SOURCE_CODE = """type('X', (a if c else b), {})
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernarySetattrThreeArgs(ExhaustiveTestCase):
    """Bug R15 (new): setattr(obj, (a if c else b), 1) — setattr 三参数 ternary 在中间。

    原始:
        setattr(obj, (a if c else b), 1)
    缺陷: ternary 作为 setattr 第二位置参数（属性名），前后是 obj 和 value。
         cond_block preload 含 PUSH_NULL + LOAD setattr + LOAD obj，ternary
         merge 块栈顶与 LOAD_CONST 1 一起 PRECALL + CALL 3 消费。
    """
    SOURCE_CODE = """setattr(obj, (a if c else b), 1)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryStrJoin(ExhaustiveTestCase):
    """Bug R15 (new): ",".join((a if c else b)) — str.join 单 ternary 参数。

    原始:
        ",".join((a if c else b))
    缺陷: ternary 作为 str.join 单参数（带括号）。cond_block preload 含
         LOAD_CONST "," + LOAD_ATTR join，ternary merge 块栈顶由 PRECALL +
         CALL 1 消费。R13 已测 method chain + ternary，但此处是 str 字面量
         的 .method(ternary) 模式（无 obj Name，obj 是 Constant）。
    """
    SOURCE_CODE = '''",".join((a if c else b))
'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

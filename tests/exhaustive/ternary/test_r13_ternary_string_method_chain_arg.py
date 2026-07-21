import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryStringMethodChainArg(ExhaustiveTestCase):
    """Bug R13 (new): s.upper().split((a if c else b)) — string method chain arg ternary。

    原始:
        s.upper().split((a if c else b))
    缺陷: ternary 作为 string method chain 中第二个方法 (split) 的位置参数。
         cond_block preload 含 PUSH_NULL + LOAD_NAME s + LOAD_ATTR upper +
         PRECALL + CALL 0 + LOAD_ATTR split。ternary merge 块栈输出作为
         split 调用第一个位置参数。R12 已修 max(default=ternary) 的 kwarg
         + preload 模式，R13 测 method chain 中间环节的 LOAD_ATTR 方法
         调用 + ternary arg。
    """
    SOURCE_CODE = """s.upper().split((a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

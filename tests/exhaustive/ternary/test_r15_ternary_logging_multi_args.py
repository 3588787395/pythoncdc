import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryLoggingMultiArgs(ExhaustiveTestCase):
    """Bug R15 (new): logging.info("%s %s", (a if c else b), x) — logging 多参数。

    原始:
        logging.info("%s %s", (a if c else b), x)
    缺陷: ternary 作为 logging.info 第二位置参数（带括号），格式串 + x 作为
         sibling 位置参数。cond_block preload 含 PUSH_NULL + LOAD logging +
         LOAD_ATTR info + LOAD_CONST "%s %s"，ternary merge 块栈顶与 LOAD x
         一起 PRECALL + CALL 3。R13 已测 ternary_method_chain_arg，但此处
         是 logging 模块的 attribute call + 多位置参数。
    """
    SOURCE_CODE = """logging.info("%s %s", (a if c else b), x)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

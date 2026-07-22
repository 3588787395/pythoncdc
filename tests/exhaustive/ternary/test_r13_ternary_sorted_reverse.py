import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernarySortedReverse(ExhaustiveTestCase):
    """Bug R13 (new): sorted(x, reverse=(a if c else b)) — sorted kwarg ternary。

    原始:
        sorted(x, reverse=(a if c else b))
    缺陷: ternary 作为 sorted 内置函数的 keyword 参数 reverse=ternary。
         cond_block preload 含 PUSH_NULL + LOAD_GLOBAL sorted + LOAD_NAME x
         （位置参数），ternary merge 块作为 KW_NAMES 对应的 kwarg value。
         与 R12 max_default 模式同根因：preload 位置参数 x 与 kwarg=ternary 共存。
         R12 已修 max default 场景，R13 测 sorted reverse 场景验证修复普适性。
    """
    SOURCE_CODE = """sorted(x, reverse=(a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

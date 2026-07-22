import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryGetattrTwoArgs(ExhaustiveTestCase):
    """Bug R15 (new): getattr(obj, (a if c else b)) — getattr 末位 ternary。

    原始:
        getattr(obj, (a if c else b))
    缺陷: ternary 作为 getattr 第二位置参数（属性名），obj 作为第一位置参数。
         cond_block preload 含 PUSH_NULL + LOAD getattr + LOAD obj，ternary
         merge 块栈顶由 PRECALL + CALL 2 消费。与 map/filter 同模式但 getattr
         是不同内置。
    """
    SOURCE_CODE = """getattr(obj, (a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

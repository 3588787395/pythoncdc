import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryAsyncAenter(ExhaustiveTestCase):
    """Bug R10-14 (re-verify in R11): async __aenter__ + ternary in body.

    原始:
        class C:
            async def __aenter__(self):
                self.x = (a if c else b)
                return self
    缺陷: __aenter__ 方法体内 ternary 赋值。ternary merge 块的 STORE_ATTR x
         与后续 RETURN_VALUE 在同一 code object。async 方法体内 ternary 区域
         归约是否正确。依「父引用子入口」：父 Assign 通过 STORE_ATTR x 引用
         ternary 子节点作为右值。
    """
    SOURCE_CODE = """class C:
    async def __aenter__(self):
        self.x = (a if c else b)
        return self
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

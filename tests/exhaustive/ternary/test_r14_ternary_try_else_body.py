import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryTryElseBody(ExhaustiveTestCase):
    """Bug R14 (new): try else: x = (a if c else b) — try-else 体含 ternary。

    原始:
        try:
            pass
        except:
            pass
        else:
            x = (a if c else b)
    缺陷: try-else 块体含 ternary 赋值。R7 try_else 已测 try-else + ternary。
         R14 测 try-else body 内 ternary 直接赋值变体：try 块无异常时 JUMP_FORWARD
         跳过 except 块到 else 块，ternary region 在 else 块入口可能与
         try-except region 边界冲突。
    """
    SOURCE_CODE = """try:
    pass
except:
    pass
else:
    x = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

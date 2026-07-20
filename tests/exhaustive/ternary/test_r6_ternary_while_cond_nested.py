import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryWhileCondNested(ExhaustiveTestCase):
    """Bug R6: 嵌套 ternary 在 while 条件中 — 字节码不一致。

    原始:
        while (a if c else (b if d else e)):
            pass
    缺陷: R5-05/06/07 已识别 while(ternary) 为已知限制（ternary 条件
         与 while 循环条件融合，违反「每块唯一归属」）。R6 用嵌套 ternary
         (a if c else (b if d else e)) 加重复杂度，期望暴露嵌套 ternary
         在 while 条件中的额外问题。
    """
    SOURCE_CODE = """while (a if c else (b if d else e)):
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

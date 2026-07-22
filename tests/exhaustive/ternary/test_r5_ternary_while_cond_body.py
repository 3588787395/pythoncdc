import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryWhileCondBody(ExhaustiveTestCase):
    """Bug R5-06: ternary 作为 while 条件（带循环体赋值）— 字节码不一致。

    原始:
        while (a if c else b):
            x = 1
    缺陷: R4-10 已识别为已知限制（完全回滚）。R5 用带循环体赋值的场景，
         在 R5-05 基础上加重循环体复杂度，分离 while(ternary) + body 双重结构。
    """
    SOURCE_CODE = """while (a if c else b):
    x = 1
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

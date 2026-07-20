import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryWhileCondSimple(ExhaustiveTestCase):
    """Bug R5-05: ternary 作为 while 条件（空循环体）— 字节码不一致。

    原始:
        while (a if c else b):
            pass
    缺陷: R4-10 已识别为已知限制（完全回滚）：while(ternary) 模式中 ternary 的
         true/false blocks 同时充当 while 条件测试，违反「每块唯一归属」原则。
         R5 用空循环体（pass）作为最简场景，分离根因。
    """
    SOURCE_CODE = """while (a if c else b):
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

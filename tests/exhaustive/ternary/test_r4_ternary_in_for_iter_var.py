import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryInForIterVar(ExhaustiveTestCase):
    """Bug R4-23: ternary 作为 for 迭代器（变量对变量，无空列表常量）— 字节码不一致。

    原始:
        for x in (a if cond else b):
            pass
    缺陷: ternary 作为 for 循环迭代器时，GET_ITER 在 merge_block 中消费
         ternary 结果。R2 已测 (items if cond else [])，R4 用变量对变量排除
         空列表常量折叠干扰。反编译器可能丢失 for 结构或 ternary 结构。
    """
    SOURCE_CODE = """for x in (a if cond else b):
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

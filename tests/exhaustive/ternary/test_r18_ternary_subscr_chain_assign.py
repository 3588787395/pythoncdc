import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR18TernarySubscrChainAssign(ExhaustiveTestCase):
    """Bug R18-08: x[a if c else b][d if e else f] = 1 — chained subscript target 含两个 ternary。

    原始:
        x[a if c else b][d if e else f] = 1
    缺陷: STORE_SUBSCR 的 target 是链式 subscript x[ternary1][ternary2]，
         两个 ternary 分别是两层 BINARY_SUBSCR 的下标。R17 subscr_target_and_value
         测过单层 subscript target + value 均为 ternary。本用例 target 是两层
         subscript 各含一个 ternary：第一个 ternary merge 块的 BINARY_SUBSCR
         之后还需 LOAD_NAME x[merge1] + 第二个 ternary + BINARY_SUBSCR + STORE_SUBSCR。
         反编译退化为两段独立 POP_TOP 表达式，字节码指令数不匹配 (13 vs 10)。
    """
    SOURCE_CODE = """x[a if c else b][d if e else f] = 1
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

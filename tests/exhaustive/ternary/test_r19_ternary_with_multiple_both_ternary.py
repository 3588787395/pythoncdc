import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR19TernaryWithMultipleBothTernary(ExhaustiveTestCase):
    """Bug R19-03: with open(t1) as f, open(t2) as h — multi-with 两个 item 均含 ternary 调用参数。

    原始:
        with open(a if c else b) as f, open(d if e else g) as h:
            pass
    缺陷: multi-with 两个 with-item 的 context manager 调用 open(...) 各含一个
         ternary 位置参数。R14 with_multiple_second_as 测过 `with a as x,
         (ternary) as y` (仅第二 item 的 cm 是 ternary，第一 item cm 是常量 a)。
         本用例两个 item 的 cm 都是 open(ternary) 调用：两个 ternary merge 块
         先后汇聚到各自 BEFORE_WITH + STORE_NAME，再叠加 WITH_EXCEPT_START 清理
         链，反编译完全丢失两个 ternary 与第二 with-item，退化为
         `with context() as f: pass`。
    """
    SOURCE_CODE = """with open(a if c else b) as f, open(d if e else g) as h:
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

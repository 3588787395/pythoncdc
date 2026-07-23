import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR20TernaryWalrusInCond(ExhaustiveTestCase):
    """Bug R20-01: x = (n := a) if (m := b if c else d) else e — 双 walrus + 嵌套 ternary in cond。

    原始:
        x = (n := a) if (m := b if c else d) else e
    缺陷: ternary 的条件本身是 walrus 表达式 (m := (b if c else d))，body 是
         walrus (n := a)。R8 walrus_assign 测过 (n := (ternary)) (walrus 包裹
         整个 ternary)，R2 walrus_in_cond 测过 a if (n := x) else b (walrus
         在 cond 但非 ternary)。本用例 cond 是 walrus(嵌套ternary)：cond_block
         含外层 COPY+STORE m 消费内层 ternary merge 结果，body 含 COPY+STORE n
         消费 a，反编译退化为 `if (m := b if c else d): pass`，丢失外层三元
         的 body (n := a) 与 orelse e，字节码指令数不匹配 (13 vs 10)。
    """
    SOURCE_CODE = """x = (n := a) if (m := b if c else d) else e
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

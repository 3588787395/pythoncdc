import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR18TernaryBodyCallWithKwargs(ExhaustiveTestCase):
    """Bug R18-13: x = (a if c else b)(key=val) — ternary 作 callable 带 kwargs。

    原始:
        x = (a if c else b)(key=val)
    缺陷: ternary 本身是函数调用 (a if c else b)(...) 的 callable，且调用
         含 keyword 参数 key=val。R15 callable_no_args 测过 `(ternary)()`，
         R15 callable_multi_args 测过 `(ternary)(x, y)` (位置参数)。
         本用例含 kwargs：merge 块的 KW_NAMES + PRECALL + CALL 消费链与
         ternary 的 func 槽位归属冲突。反编译丢失 ternary callable 与 kwarg，
         退化为 `x = b`，字节码指令数不匹配 (12 vs 7)。
    """
    SOURCE_CODE = """x = (a if c else b)(key=val)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

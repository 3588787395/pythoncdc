import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3TernaryRaiseFrom(ExhaustiveTestCase):
    """Bug R3-16: ternary 在 raise ... from ... 的 from 子句 — 字节码不一致。

    原始: raise E1 from (E2 if cond else E3)
    缺陷: ternary 在 raise from 子句中时，RAISE_VARARGS 1 消费 ternary 结果，
         同时 __context__ 设置需 JOIN_KERNEL 等指令。反编译器可能丢失 from 结构。
    """
    SOURCE_CODE = """raise E1 from (E2 if cond else E3)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInRaise(ExhaustiveTestCase):
    """Bug R2-5: ternary 在 raise 语句中 — 字节码不一致。

    原始: raise (Exc1 if cond else Exc2)()
    缺陷: ternary 在 raise 语句中时，RAISE_VARARGS 在 merge_block 中消费
         ternary 结果（已通过 CALL 调用过的实例）。反编译器可能丢失 raise 结构。
    """
    SOURCE_CODE = """raise (Exc1 if cond else Exc2)()"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

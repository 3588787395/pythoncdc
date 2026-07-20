import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR3TernaryRaiseArg(ExhaustiveTestCase):
    """Bug R3-20: ternary 作为 raise 异常的构造参数 — 字节码不一致。

    原始: raise E(a if cond else b)
    缺陷: ternary 作为 raise 异常构造函数参数时，CALL + RAISE_VARARGS 1
         在 merge_block 中消费 ternary 结果。反编译器可能丢失 raise 结构。
    """
    SOURCE_CODE = """raise E(a if cond else b)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

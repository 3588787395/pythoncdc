import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInMultiArgCall(ExhaustiveTestCase):
    """Bug R2-37: ternary 作为函数调用的第二个参数 — 字节码不一致。

    原始: print(prefix, a if cond else b)
    缺陷: ternary 作为函数调用的第二个参数时，第一个参数 prefix 在 ternary entry
         之前被加载并"困"在栈上，CALL 同时消费 prefix 和 ternary 结果。
         反编译器可能丢失 prefix 参数。
    """
    SOURCE_CODE = """print(prefix, a if cond else b)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

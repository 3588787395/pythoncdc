import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInFuncCall(ExhaustiveTestCase):
    """Bug R2-12: ternary 作为函数调用参数（PUSH_NULL + LOAD 模式） — 字节码不一致。

    原始: print(a if cond else b)
    缺陷: ternary 作为 print 函数调用参数时，PUSH_NULL + LOAD_NAME print 在
         ternary entry 之前，PRECALL + CALL 在 merge_block。
         反编译器可能丢失 print() 调用结构。
    """
    SOURCE_CODE = """print(a if cond else b)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryMethodChain(ExhaustiveTestCase):
    """Bug R2-35: ternary 作为方法链调用的对象 — 字节码不一致。

    原始: x = (a if cond else b).method().attr
    缺陷: ternary 作为方法链调用的对象时，LOAD_ATTR/LOAD_METHOD/PRECALL/CALL
         + LOAD_ATTR 序列在 merge_block 中消费 ternary 结果。
         反编译器可能丢失方法链结构。
    """
    SOURCE_CODE = """x = (a if cond else b).method().attr"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryInDelTarget(ExhaustiveTestCase):
    """Bug R4-22: ternary 作为 del subscript 目标索引 — 字节码不一致。

    原始: del x[a if cond else b]
    缺陷: ternary 作为 del 的 subscript 索引时，DELETE_SUBSCR 在 merge_block
         中消费 ternary 结果与 subscript 对象。R2 已测 store_subscr，R4 测 del
         场景以分离 DELETE_SUBSCR 与 STORE_SUBSCR 的指令处理差异。
         反编译器可能丢失 del 结构或 ternary 结构。
    """
    SOURCE_CODE = """del x[a if cond else b]"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

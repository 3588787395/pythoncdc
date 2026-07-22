import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryInDictKey(ExhaustiveTestCase):
    """Bug R4-21: ternary 作为 dict key（与 R1/R2 value 场景对照）— 字节码不一致。

    原始: d = {(a if cond else b): 1}
    缺陷: ternary 作为 dict 的 key 时，BUILD_MAP 在 merge_block 中消费
         ternary 结果作为 key、常量 1 作为 value。R1/R2 已测 ternary 作为 value，
         R4 测 ternary 作为 key 以分离栈序与 dict key 顺序的根因。
         反编译器可能丢失 dict 结构或 key/value 顺序错乱。
    """
    SOURCE_CODE = """d = {(a if cond else b): 1}"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

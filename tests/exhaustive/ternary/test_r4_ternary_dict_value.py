import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryDictValue(ExhaustiveTestCase):
    """Bug R4-08: ternary 作为 dict 多 value（多 key 场景）— 字节码不一致。

    原始: d = {k: a if cond else b, k2: c if d else e}
    缺陷: 多个 ternary 作为 dict value 时，BUILD_MAP 在 merge_block 中消费
         多组 (key, value) 对。两个 ternary 共享或分离 merge_block 的处理
         在多 key 场景下更复杂。反编译器可能丢失 dict 结构或多 ternary 结构。
    """
    SOURCE_CODE = """d = {k: a if cond else b, k2: c if d else e}"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

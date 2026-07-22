import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryInDictComp(ExhaustiveTestCase):
    """Bug R5-19: dictcomp 含 ternary value — 字节码不一致。

    原始: d = {k: (a if c else b) for k in xs}
    缺陷: ternary 作为 dictcomp value 时，MAP_ADD 在内嵌 code object 的
         merge_block 中消费 ternary 结果。R2 已通过 ternary dictcomp 场景
         （test_r2_ternary_in_dictcomp）。R5 用单迭代变量 + 简化 key 形式重测，
         分离根因。期望：DictComp(key=k, value=IfExp) 正确归约。
    """
    SOURCE_CODE = """d = {k: (a if c else b) for k in xs}"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

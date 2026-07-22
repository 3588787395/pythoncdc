import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryInGenexp(ExhaustiveTestCase):
    """Bug R5-21: genexp 含 ternary element — 字节码不一致。

    原始: g = (a if c else b for i in range(10))
    缺陷: ternary 作为 genexp element 时，YIELD_VALUE 在内嵌 code object 的
         merge_block 中消费 ternary 结果。R2 已通过 listcomp/set/dict 等场景，
         但 genexp 形式（生成器表达式）尚未测试。R5 用 genexp 形式重测。
         期望：GeneratorExp(elt=IfExp) 正确归约。
    """
    SOURCE_CODE = """g = (a if c else b for i in range(10))"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

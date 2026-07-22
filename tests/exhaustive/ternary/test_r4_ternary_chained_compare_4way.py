import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryChainedCompare4Way(ExhaustiveTestCase):
    """Bug R4-02: ternary 在 4-term chained compare 中段（变体）— 字节码不一致。

    原始: r = 0 < (a if cond else b) < 10 < 100
    缺陷: ternary 在 4-term chained compare 中段时，需多次 COPY 2 复制 ternary
         结果供后续比较段使用。反编译器可能丢失 chained compare 结构。
         R3 已识别为已知限制（R3-02），R4 使用变量 b 替代常量 1 排除常量折叠干扰。
    """
    SOURCE_CODE = """r = 0 < (a if cond else b) < 10 < 100"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

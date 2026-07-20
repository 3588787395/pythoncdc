import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryChainedCompareLeft(ExhaustiveTestCase):
    """Bug R4-01: ternary 在 chained compare 左端（2-term）— 字节码不一致。

    原始: r = (a if cond else b) < 10
    缺陷: ternary 在 chained compare 左端时，COPY 2 复制 ternary 结果供后续
         比较段使用。反编译器可能丢失 chained compare 结构或 ternary 结构。
         R3 已识别为已知限制（R3-01），R4 在 2-term 简化场景下重测以分离根因。
    """
    SOURCE_CODE = """r = (a if cond else b) < 10"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

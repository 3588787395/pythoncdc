import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryExceptionGroup(ExhaustiveTestCase):
    """Bug R9: except* handler body 含 ternary — 字节码不一致。

    原始:
        try:
            pass
        except* E as e:
            x = a if c else b
    缺陷: Python 3.11+ except* (PEP 654) handler body 含 ternary 赋值。
         except* 的 PUSH_EXC_INFO + CHECK_EG_MATCH + COPY 路径与 ternary
         merge 块的 STORE_FAST x 在同一 handler body，可能暴露 except*
         handler region 与 ternary region 的归属冲突。
    """
    SOURCE_CODE = """try:
    pass
except* E as e:
    x = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

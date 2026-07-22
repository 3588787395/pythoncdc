import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryInAssertDictMsg(ExhaustiveTestCase):
    """Bug R8: assert 的 message 是 dict 含 ternary — 字节码不一致。

    原始:
        assert x, {k: (a if c else b)}
    缺陷: assert 的 message 位置是 dict 字面量，其 value 是 ternary。
         R7-01 已知简单 assert message ternary 失败。R8 测 dict 包装变体：
         dict 的 BUILD_MAP + LOAD key/value 与 ternary merge 块的
         LOAD_ASSERTION_ERROR + RAISE_VARARGS 路径共享同一 merge_block，
         可能暴露 dict 重建与 assert raise 基础设施指令过滤的冲突。
    """
    SOURCE_CODE = """assert x, {k: (a if c else b)}
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryInAssertWalrusMsg(ExhaustiveTestCase):
    """Bug R8: assert 的 message 是 walrus(ternary) — 字节码不一致。

    原始:
        assert x, (n := (a if c else b))
    缺陷: assert 的 message 位置使用 walrus 表达式捕获 ternary 结果。
         R7-01 已知 assert message ternary 失败（LOAD_NAME/RAISE_VARARGS
         顺序错乱）。R8 测 walrus 包装变体：walrus 的 COPY+STORE 副作用
         与 ternary merge 块的 LOAD_ASSERTION_ERROR + RAISE_VARARGS 路径
         共享同一 merge_block，可能暴露 walrus 重建与 assert raise
         基础设施指令过滤的冲突。
    """
    SOURCE_CODE = """assert x, (n := (a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

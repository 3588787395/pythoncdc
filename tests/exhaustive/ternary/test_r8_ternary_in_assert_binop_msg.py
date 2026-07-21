import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryInAssertBinopMsg(ExhaustiveTestCase):
    """Bug R8: assert 的 message 是字符串拼接 ternary — 字节码不一致。

    原始:
        assert x, "msg: " + (a if c else b)
    缺陷: assert 的 message 位置是字符串 + ternary 的 BINARY_OP。
         R7-01 已知简单 assert message ternary 失败。R8 测 BINARY_OP
         包装变体：BINARY_OP 在 merge_block 消费 ternary 结果与
         LOAD_CONST "msg: "，与 LOAD_ASSERTION_ERROR + RAISE_VARARGS
         路径共享同一 merge_block，可能暴露 BINARY_OP 重建与 assert
         raise 基础设施指令过滤的冲突。
    """
    SOURCE_CODE = """assert x, "msg: " + (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

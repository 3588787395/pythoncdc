import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1AssertSimple(ExhaustiveTestCase):
    """Bug 3: assert(ternary) — assert 中三元表达式反编译验证。

    原始: assert (a if a > 0 else b)
    说明: assert 的参数是 IfExp 表达式。当 else 分支为变量时，
         CPython 编译器保留完整的 ternary 字节码结构
         (cond_block + body + else_block + assert check)，
         反编译器应正确恢复 IfExp AST 节点。

    注: 当 else 为 falsy 常量（如 0/None/False）时，CPython 编译器
         会优化掉 else 分支，使 `assert (a if cond else 0)` 与
         `assert (cond and a)` 产生完全相同的字节码，二者语义等价、
         字节码层面不可区分。此时反编译为 BoolOp 是正确的（语义等价）。
         本用例使用 else=变量 b 以测试可区分场景下的 IfExp 恢复。
    """
    SOURCE_CODE = """assert (a if a > 0 else b)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

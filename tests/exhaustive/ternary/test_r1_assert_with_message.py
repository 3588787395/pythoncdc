import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1AssertWithMessage(ExhaustiveTestCase):
    """Bug 4: assert(ternary, msg) — 带消息的 assert 中三元反编译验证。

    原始: assert (a if cond else b), "error"
    说明: assert 语句的第一个参数是 IfExp，第二个参数是 message。
         当 else 分支为变量时，字节码保留完整 ternary 结构，
         反编译器应正确恢复 IfExp 并保留 message 参数。

    注: 与 Bug 3 同源。当 else 为 falsy 常量时字节码不可区分
         （CPython 优化），本用例使用 else=变量 b 以测试可区分场景。
    """
    SOURCE_CODE = '''assert (a if cond else b), "error"'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryWhileBodyTernary(ExhaustiveTestCase):
    """Bug R6: ternary 在 while body 中（非条件）— 字节码不一致。

    原始:
        while x:
            y = a if c else b
    缺陷: 区别于 R5-05/06/07（ternary 在 while 条件中），本测试将 ternary
         放在 while body 中作为赋值表达式。期望 ternary 不应与 while 循环
         结构融合；当前疑似 while body 内 ternary 与 loop test 共享块导致
         归属冲突。
    """
    SOURCE_CODE = """while x:
    y = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

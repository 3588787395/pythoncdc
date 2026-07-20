import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryInAssert(ExhaustiveTestCase):
    """Bug R4-20: ternary 作为 assert 测试表达式 — 字节码不一致。

    原始: assert (a if cond else b), "msg"
    缺陷: ternary 作为 assert 的测试表达式时，POP_JUMP_IF_TRUE 在 merge_block
         中消费 ternary 结果决定是否抛出 AssertionError。R1 已测 assert_simple
         （ternary 在 message），R4 测 ternary 在 test 位置。
         反编译器可能丢失 assert 结构或 ternary 结构。
    """
    SOURCE_CODE = '''assert (a if cond else b), "msg"'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInImportTest(ExhaustiveTestCase):
    """Bug R7: ternary 两分支都是 __import__ 调用 — 字节码不一致。

    原始:
        x = __import__('os') if c else __import__('sys')
    缺陷: ternary 的 true/false value 都是 __import__ 调用。两个分支
         都使用 PUSH_NULL + LOAD_NAME __import__ + LOAD_CONST str +
         PRECALL + CALL 模式，两条调用链在各自的 value block 中，
         外层 merge_block 的 STORE_NAME x 消费 ternary 结果。
         期望 ternary 正确归约为 IfExp(__import__('os'), __import__('sys'))；
         当前疑似两个分支的 PUSH_NULL 前缀让 condition_block 推断
         失败，进而 ternary 退化为 if-else + 表达式泄漏。
    """
    SOURCE_CODE = """x = __import__('os') if c else __import__('sys')
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

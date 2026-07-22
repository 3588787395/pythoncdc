import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryInFormat(ExhaustiveTestCase):
    """Bug R4-15: ternary 在 str.format() 多参数调用 — 字节码不一致。

    原始: x = "{}-{}".format(a if cond else b, c if d else e)
    缺陷: 多个 ternary 作为 .format() 位置参数时，LOAD_ATTR + PRECALL + CALL
         在 merge_block 中消费多个 ternary 结果。两个 ternary 通过 chained
         container 模式合并到 format 调用。
         反编译器可能丢失 .format() 调用结构或多 ternary 结构。
    """
    SOURCE_CODE = '''x = "{}-{}".format(a if cond else b, c if d else e)'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

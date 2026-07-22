import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryInPrint(ExhaustiveTestCase):
    """Bug R4-13: ternary 在 print 多参数（混合常量与 ternary）— 字节码不一致。

    原始: print(a if cond else b, c if d else e)
    缺陷: 多个 ternary 作为 print 位置参数时，PRECALL + CALL 在 merge_block
         中消费多个 ternary 结果。两个 ternary 通过 chained container 模式
         或独立 merge_block 链合并到 print 调用。
         反编译器可能丢失 print 结构或多 ternary 结构。
    """
    SOURCE_CODE = """print(a if cond else b, c if d else e)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryInCallKwargs(ExhaustiveTestCase):
    """Bug R4-16: ternary 在函数调用多 kwargs（KWARGS_OP）— 字节码不一致。

    原始: f(x=a if cond else b, y=c if d else e)
    缺陷: 多个 ternary 作为函数调用关键字参数时，KWARGS_OP（BUILD_MAP +
         KW_NAMES）在 merge_block 中消费多个 ternary 结果。两个 ternary
         共享或分离 merge_block 的处理在 kwargs 场景下更复杂。
         反编译器可能丢失 kwargs 结构或多 ternary 结构。
    """
    SOURCE_CODE = """f(x=a if cond else b, y=c if d else e)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

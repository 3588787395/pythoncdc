import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryBytesJoin(ExhaustiveTestCase):
    """Bug R15 (new): b",".join((a if c else b)) — bytes.join 单 ternary 参数。

    原始:
        b",".join((a if c else b))
    缺陷: ternary 作为 bytes.join 单参数（带括号）。cond_block preload 含
         LOAD_CONST b"," + LOAD_ATTR join，ternary merge 块栈顶由 PRECALL +
         CALL 1 消费。R15 str_join 测 str 字面量 .join，本测试测 bytes 字面量
         .join 变体（LOAD_CONST 的 argval 是 bytes 而非 str）。
    """
    SOURCE_CODE = '''b",".join((a if c else b))
'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

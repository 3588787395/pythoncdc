import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR17TernaryMethodArgThenAttr(ExhaustiveTestCase):
    """Bug R17-06: obj.method(a if c else b).other — method call with ternary arg then attr。

    原始:
        obj.method(a if c else b).other
    缺陷: ternary 作为 obj.method() 的参数，调用结果再 .other 取属性。
         cond_block preload 含 LOAD obj + LOAD_METHOD method，ternary merge 块
         栈顶经 PRECALL + CALL + LOAD_ATTR other + POP_TOP 消费链。
         _try_build_ternary_merge_consumer_expr 未处理「CALL 后再 LOAD_ATTR」
         的后续属性访问，丢失 .other，字节码指令数不匹配 (12 vs 11)。
    """
    SOURCE_CODE = """obj.method(a if c else b).other
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

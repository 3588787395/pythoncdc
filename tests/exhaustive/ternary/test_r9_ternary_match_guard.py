import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryMatchGuard(ExhaustiveTestCase):
    """Bug R9: match case guard 是 ternary — 字节码不一致。

    原始:
        match x:
            case 1 if (a if c else b):
                pass
    缺陷: match 语句的 case guard 是 ternary。Python 3.10+ match 的
         MATCH_CLASS + COMPARE_OP + POP_JUMP_IF_FALSE 路径与 ternary
         的 condition/true/false merge 路径在 guard 位置嵌套，可能
         暴露 match region 与 ternary region 的归属冲突。
    """
    SOURCE_CODE = """match x:
    case 1 if (a if c else b):
        pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryMatchSubject(ExhaustiveTestCase):
    """Bug R14 (new): match (a if c else b): case 1: pass — match 主体是 ternary。

    原始:
        match (a if c else b):
            case 1:
                pass
    缺陷: match 语句的主体表达式是 ternary。match 编译为：先求值 subject
         （ternary merge 块栈顶），COPY 1 + MATCH_MAPPING/MATCH_SEQUENCE 等
         pattern matching 指令消费 subject。R9 测过 match_guard (case guard 是
         ternary)。R14 测 match subject 是 ternary 的反方向变体：ternary 在
         subject 位置而非 case guard 位置。
    """
    SOURCE_CODE = """match (a if c else b):
    case 1:
        pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

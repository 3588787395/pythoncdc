import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR18TernaryMatchGuardWildcard(ExhaustiveTestCase):
    """Bug R18-04: match x: case _ if (a if c else b): pass — wildcard case guard 是 ternary。

    原始:
        match x:
            case _ if (a if c else b):
                pass
    缺陷: match 语句的通配符 case _ 的 guard 是 ternary。R9 match_guard 测过
         `case 1 if (ternary)` (具体字面量模式，MATCH_VALUE 路径) 并通过。
         本用例 case _ 通配符不产生 MATCH_VALUE，guard 的 ternary 直接挂在
         case body 入口前。通配符 case 的 case_body 块与 ternary 的
         condition/true/false/merge 块归属冲突，反编译退化为破碎的嵌套 if，
         字节码参数不匹配 (LOAD_NAME c vs a)。
    """
    SOURCE_CODE = """match x:
    case _ if (a if c else b):
        pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

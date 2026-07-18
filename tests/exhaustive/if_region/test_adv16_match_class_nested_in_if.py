import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv16MatchClassNestedInIf(ExhaustiveTestCase):
    # if 体内 match 类模式嵌套（类模式的属性也是类模式）：
    # if c:
    #     match p:
    #         case Outer(x=Inner(1)):
    #             pass
    #         case _:
    #             pass
    # 字节码 MATCH_CLASS + 嵌套 MATCH_CLASS / 反编译器在 if body 内
    # match 嵌套类模式时的多层结构归约。
    SOURCE_CODE = """if c:
    match p:
        case Outer(x=Inner(1)):
            pass
        case _:
            pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

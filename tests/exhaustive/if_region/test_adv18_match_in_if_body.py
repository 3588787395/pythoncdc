import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18MatchInIfBody(ExhaustiveTestCase):
    # if body 内含 match-case + guard 复杂结构：
    # def f(x):
    #     if flag:
    #         match x:
    #             case [a, b] if a > b:
    #                 return 'descending'
    #             case [a, b]:
    #                 return 'ascending'
    #             case _:
    #                 return 'other'
    #     return None
    # 字节码 MATCH_CLASS / POP_JUMP_IF_FALSE + guard 的 POP_JUMP_IF_FALSE
    # / 反编译器在 if body 内 match-case + guard 时易把 guard 错挂到 if body 外。
    SOURCE_CODE = """def f(x):
    if flag:
        match x:
            case [a, b] if a > b:
                return 'descending'
            case [a, b]:
                return 'ascending'
            case _:
                return 'other'
    return None"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

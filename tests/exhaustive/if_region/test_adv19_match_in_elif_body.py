import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19MatchInElifBody(ExhaustiveTestCase):
    # elif body 内含 match-case（R18 只测了 if body 内 match）：
    # def f(x, kind):
    #     if x > 0:
    #         return 'pos'
    #     elif kind == 'check':
    #         match x:
    #             case 0:
    #                 return 'zero_kind'
    #             case -1:
    #                 return 'neg_one_kind'
    #             case _:
    #                 return 'other_kind'
    #     else:
    #         return 'neg'
    # 字节码 MATCH_SEQUENCE / MATCH_CLASS / POP_JUMP_IF_FALSE
    # / 反编译器在 elif body 内 match-case 时易把 case 错挂到 if 外。
    SOURCE_CODE = """def f(x, kind):
    if x > 0:
        return 'pos'
    elif kind == 'check':
        match x:
            case 0:
                return 'zero_kind'
            case -1:
                return 'neg_one_kind'
            case _:
                return 'other_kind'
    else:
        return 'neg'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

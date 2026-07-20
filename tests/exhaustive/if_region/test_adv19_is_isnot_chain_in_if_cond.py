import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19IsIsnotChainInIfCond(ExhaustiveTestCase):
    # if-elif-else 条件含 `is` / `is not` 链 + None 检查 + elif：
    # def f(a, b, c):
    #     if a is None and b is None and c is None:
    #         return 'all_none'
    #     elif a is not None or b is not None:
    #         return 'some_not_none'
    #     elif c is None:
    #         return 'c_none'
    #     else:
    #         return 'none'
    # 字节码 IS_OP / POP_JUMP_IF_FALSE / POP_JUMP_IF_TRUE
    # / 反编译器在 3 项 is/is not 链 + elif 链时易归约错乱。
    SOURCE_CODE = """def f(a, b, c):
    if a is None and b is None and c is None:
        return 'all_none'
    elif a is not None or b is not None:
        return 'some_not_none'
    elif c is None:
        return 'c_none'
    else:
        return 'none'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

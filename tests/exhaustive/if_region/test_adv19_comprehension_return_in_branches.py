import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19ComprehensionReturnInBranches(ExhaustiveTestCase):
    # if-elif-else 三分支各自返回不同类型的 comprehension：
    # def f(flag, items):
    #     if flag == 'list':
    #         return [x * 2 for x in items if x > 0]
    #     elif flag == 'set':
    #         return {x * 2 for x in items if x > 0}
    #     elif flag == 'dict':
    #         return {x: x * 2 for x in items if x > 0}
    #     else:
    #         return (x * 2 for x in items if x > 0)
    # 字节码 LIST_COMP / SET_COMP / DICT_COMP / GET_ITER / FOR_ITER
    # / 反编译器在 if-elif-else 三分支都返回 comprehension 时易归约错乱。
    SOURCE_CODE = """def f(flag, items):
    if flag == 'list':
        return [x * 2 for x in items if x > 0]
    elif flag == 'set':
        return {x * 2 for x in items if x > 0}
    elif flag == 'dict':
        return {x: x * 2 for x in items if x > 0}
    else:
        return (x * 2 for x in items if x > 0)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

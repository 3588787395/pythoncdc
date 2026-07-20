import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20TupleReturnInBranches(ExhaustiveTestCase):
    # if-elif-else 三分支各自返回多元素 tuple + 嵌套结构：
    # def f(flag, x):
    #     if flag == 'a':
    #         return (x, x + 1, x * 2, [x, x + 1], {'k': x})
    #     elif flag == 'b':
    #         return ((x, x + 1), (x + 2, x + 3), [x, x + 4])
    #     else:
    #         return ((), [], {}, {x, x + 1}, (x for x in range(3)))
    # 字节码 BUILD_TUPLE / BUILD_LIST / BUILD_MAP / BUILD_SET / GET_ITER
    # / 反编译器在 if-elif-else 三分支都返回多类型嵌套 tuple 时易结构错乱。
    SOURCE_CODE = """def f(flag, x):
    if flag == 'a':
        return (x, x + 1, x * 2, [x, x + 1], {'k': x})
    elif flag == 'b':
        return ((x, x + 1), (x + 2, x + 3), [x, x + 4])
    else:
        return ((), [], {}, {x, x + 1}, (x for x in range(3)))"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

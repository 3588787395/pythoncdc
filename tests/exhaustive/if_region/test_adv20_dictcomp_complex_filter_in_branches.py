import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20DictcompComplexFilterInBranches(ExhaustiveTestCase):
    # if-elif-else 三分支各自含 dictcomp/setcomp + 多 for + if 过滤：
    # def f(flag, data):
    #     if flag == 'dict':
    #         return {k: v * 2 for k, v in data.items() if k != 'skip' for x in [v] if x > 0}
    #     elif flag == 'set':
    #         return {x % 10 for x in data if x > 0 for y in range(x) if y % 2 == 0}
    #     else:
    #         return {x: y for x in range(5) for y in range(5) if x + y == 4}
    # 字节码 BUILD_MAP / GET_ITER / FOR_ITER / POP_JUMP_IF_FALSE
    # / 反编译器在 if-elif-else 三分支都含多 for + if 的 dictcomp/setcomp 时易归约错乱。
    SOURCE_CODE = """def f(flag, data):
    if flag == 'dict':
        return {k: v * 2 for k, v in data.items() if k != 'skip' for x in [v] if x > 0}
    elif flag == 'set':
        return {x % 10 for x in data if x > 0 for y in range(x) if y % 2 == 0}
    else:
        return {x: y for x in range(5) for y in range(5) if x + y == 4}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

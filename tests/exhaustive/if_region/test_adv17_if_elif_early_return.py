import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv17IfElifEarlyReturn(ExhaustiveTestCase):
    # if/elif 链配合 early return + 末尾 fallthrough return：
    # def f():
    #     if x:
    #         return 1
    #     elif y:
    #         return 2
    #     return 3
    # 字节码 if + elif 的 POP_JUMP_IF_FALSE 链 + 每分支 RETURN_VALUE
    # / 反编译器在 if/elif 每个 body 含 return + 函数尾部裸 return 组合时
    # 易把末尾 return 误归到 elif 的 else 分支。
    SOURCE_CODE = """def f():
    if x:
        return 1
    elif y:
        return 2
    return 3"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

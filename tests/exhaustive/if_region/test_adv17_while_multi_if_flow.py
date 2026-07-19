import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv17WhileMultiIfFlow(ExhaustiveTestCase):
    # while True + 多 if + break/continue/return：
    # def f():
    #     while True:
    #         if x:
    #             break
    #         if y:
    #             continue
    #         return 1
    # 字节码 while True 的 JUMP_BACKWARD + 多 if 的 POP_JUMP_IF_FALSE
    # / 反编译器在 while body 内多个并列 if 配合不同 flow control 时
    # 易把第二个 if 错挂到第一个 if 的 else 分支，或把 return 错挂在 if body 内。
    SOURCE_CODE = """def f():
    while True:
        if x:
            break
        if y:
            continue
        return 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

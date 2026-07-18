import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv15TernaryEachBranch(ExhaustiveTestCase):
    # if/elif/else 每个分支的 body 均为三元赋值：
    # if a:
    #     x = 1 if p else 2
    # elif b:
    #     x = 3 if q else 4
    # else:
    #     x = 5 if r else 6
    # 字节码三个分支各自含三元 merge_block + STORE_NAME x。
    # 反编译器未能正确识别 if/elif/else 的分支结构与各分支内
    # 的三元赋值，将整个 if/elif/else 错误地合并为一个嵌套
    # 三元表达式 ((1 if p else 2) if a else (3 if q else 4)
    # if b else 5 if r else 6) 作为顶层表达式语句，控制流
    # 结构与赋值语义均被破坏。
    SOURCE_CODE = """if a:
    x = 1 if p else 2
elif b:
    x = 3 if q else 4
else:
    x = 5 if r else 6"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

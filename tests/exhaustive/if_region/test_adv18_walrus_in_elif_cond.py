import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18WalrusInElifCond(ExhaustiveTestCase):
    # if-elif 链中 elif 条件含 walrus 表达式：
    # if (n := len(s)) > 10:
    #     r = 'long'
    # elif (m := n // 2) > 5:
    #     r = 'mid'
    # else:
    #     r = 'short'
    # 字节码 walrus 的 COPY + STORE_NAME + POP_JUMP_IF_FALSE / 反编译器
    # 在 elif 条件含 walrus 时易丢失 walrus 绑定或错把 walrus 当独立 if。
    SOURCE_CODE = """if (n := len(s)) > 10:
    r = 'long'
elif (m := n // 2) > 5:
    r = 'mid'
else:
    r = 'short'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

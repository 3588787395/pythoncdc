import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv15WalrusTernaryCond(ExhaustiveTestCase):
    # if 条件中 walrus 直接绑定三元结果并参与比较：
    # if (n := (a if c else b)) > 0:
    #     pass
    # 字节码 LOAD_NAME c / POP_JUMP_IF_FALSE（跳到 b 分支）
    # / LOAD_NAME a / JUMP / LOAD_NAME b / COPY / STORE_NAME n
    # / LOAD_CONST 0 / COMPARE_OP > / POP_JUMP_IF_FALSE。
    # 反编译器在 walrus COPY + STORE_NAME 与三元 merge 的归约时
    # 出错，将 if 语句整体丢弃，仅保留 n = (a if c else b) 作为
    # 顶层赋值语句，比较 > 0 和 if body 完全消失。
    SOURCE_CODE = """if (n := (a if c else b)) > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

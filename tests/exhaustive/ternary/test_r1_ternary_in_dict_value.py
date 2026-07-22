import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR1TernaryInDictValue(ExhaustiveTestCase):
    """Bug 11: 多个 ternary 作为 dict value — 字节码严重不一致。

    原始: d = {"a": 1 if cond else 0, "b": 2 if cond else 0}
    错误反编译: 字节码指令数 12 vs 13，序列错位。
    缺陷: 原始用 BUILD_CONST_KEY_MAP 一次性构建字典，每个 value 是 ternary。
         反编译器未能正确重组多键 dict 字面量，丢失或错位了一个 ternary 的
         求值路径。IfExp 在 AST 中存在，但模块级字节码不一致。
    """
    SOURCE_CODE = '''d = {"a": 1 if cond else 0, "b": 2 if cond else 0}'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

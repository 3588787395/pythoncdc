import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryEnumerateStart(ExhaustiveTestCase):
    """Bug R13 (new): enumerate(x, start=(a if c else b)) — enumerate kwarg ternary。

    原始:
        enumerate(x, start=(a if c else b))
    缺陷: ternary 作为 enumerate 内置函数的 keyword 参数 start=ternary。
         与 R12 max_default 模式同根因：preload 位置参数 x + kwarg=ternary
         共存。验证 enumerate 内置函数（生成器）的 ternary kwarg 归约路径。
    """
    SOURCE_CODE = """enumerate(x, start=(a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryAnnotationDefault(ExhaustiveTestCase):
    """Bug R9: 带类型注解的变量 + ternary 默认值 — 字节码不一致。

    原始:
        x: int = (a if c else b)
    缺陷: 变量注解 AnnAssign 的 value 是 ternary。R6 已测过 annotation。
         R9 测注解 + ternary 默认值变体：ternary merge 块的 STORE_NAME x
         与注解的 LOAD_NAME int + SETUP_ANNOTATIONS 在同一 code object，
         可能暴露 AnnAssign 注解元数据与 ternary 归属的冲突。
    """
    SOURCE_CODE = """x: int = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

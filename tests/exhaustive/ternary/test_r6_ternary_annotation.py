import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryAnnotation(ExhaustiveTestCase):
    """Bug R6: ternary 在变量注解中 — 字节码不一致。

    原始: x: T = a if c else b
    缺陷: 变量注解 `x: T = ...` 在字节码中产生 SETUP_ANNOTATIONS +
         LOAD_NAME T + LOAD (ternary) + STORE_NAME x 序列。期望 ternary
         merge 块识别注解 wrapping 链；当前疑似未识别 SETUP_ANNOTATIONS，
         回退到 Expr(ternary) 或丢失注解。
    """
    SOURCE_CODE = """x: T = a if c else b"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryAssertReturnConsumer(ExhaustiveTestCase):
    """Bug R9-15 (re-verify in R11): assert + return shared ternary consumer.

    原始:
        def f():
            assert (a if c else b)
            return (x if c2 else y)
    缺陷: 同一函数体内两个 ternary，第一个 merge 含 LOAD_ASSERTION_ERROR +
         RAISE_VARARGS（assert 基础设施），第二个 merge 含 RETURN_VALUE，
         可能暴露 assert 基础设施过滤与 return ternary 识别冲突。
    """
    SOURCE_CODE = """def f():
    assert (a if c else b)
    return (x if c2 else y)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

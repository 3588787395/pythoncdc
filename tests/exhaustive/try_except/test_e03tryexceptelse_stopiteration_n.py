import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestE03TryExceptElse_StopIteration_n(ExhaustiveTestCase):
    SOURCE_CODE = """def f(n):
    try:
        next(n)
    except StopIteration:
        n = iter([])
    else:
        n = [1]"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()

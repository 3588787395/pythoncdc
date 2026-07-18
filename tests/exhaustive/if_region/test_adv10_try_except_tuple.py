import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10TryExceptTuple(ExhaustiveTestCase):
    # if 体内 try/except 捕获元组异常类型 except (E1, E2):
    SOURCE_CODE = """if c:
    try:
        x = f()
    except (ValueError, TypeError):
        x = 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

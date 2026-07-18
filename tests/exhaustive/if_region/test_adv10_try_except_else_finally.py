import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10TryExceptElseFinally(ExhaustiveTestCase):
    # if 体内 try/except/else/finally 完整组合
    SOURCE_CODE = """if c:
    try:
        x = f()
    except ValueError:
        x = 0
    else:
        y = 1
    finally:
        z = 2"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

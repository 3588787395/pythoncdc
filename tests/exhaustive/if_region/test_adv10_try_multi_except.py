import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10TryMultiExcept(ExhaustiveTestCase):
    # if 体内 try/except 多个 except 子句
    SOURCE_CODE = """if c:
    try:
        x = f()
    except ValueError:
        x = 0
    except TypeError:
        x = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

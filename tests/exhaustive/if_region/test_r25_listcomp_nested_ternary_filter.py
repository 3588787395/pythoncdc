import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25ListcompNestedTernaryFilter(ExhaustiveTestCase):
    SOURCE_CODE = """def f(items, mode):
    if mode == 'a':
        return [x for x in items if (y := x) > 0 if y < 100]
    elif mode == 'b':
        return [x if x > 0 else 0 for x in items]
    else:
        return [x for x in items if not x]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

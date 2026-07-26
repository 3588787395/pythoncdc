import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25TupleReturnComprehension(ExhaustiveTestCase):
    SOURCE_CODE = """def f(flag, items):
    if flag == 'a':
        return (sum(items), len(items), [x for x in items if x > 0])
    elif flag == 'b':
        return ({x for x in items}, {k: v for k, v in items})
    else:
        return ((x for x in items), max(items))"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

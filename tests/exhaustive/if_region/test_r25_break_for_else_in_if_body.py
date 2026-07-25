import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25BreakForElseInIfBody(ExhaustiveTestCase):
    SOURCE_CODE = """def f(items, mode):
    if mode == 'a':
        for x in items:
            if x > 100:
                break
        else:
            return 'no_big'
        return x
    elif mode == 'b':
        return 'b'
    else:
        return 'c' """
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

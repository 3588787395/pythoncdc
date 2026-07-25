import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25WhileElseContinueElifBody(ExhaustiveTestCase):
    SOURCE_CODE = """def f(items, mode):
    if mode == 'a':
        return 'a'
    elif mode == 'b':
        i = 0
        while i < len(items):
            if items[i] == 'skip':
                i += 1
                continue
            i += 1
        else:
            return 'done_b'
        return i"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

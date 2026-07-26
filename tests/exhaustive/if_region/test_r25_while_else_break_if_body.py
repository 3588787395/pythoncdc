import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25WhileElseBreakIfBody(ExhaustiveTestCase):
    SOURCE_CODE = """def f(items, mode):
    if mode == 'a':
        i = 0
        while i < len(items):
            if items[i] == 'stop':
                break
            i += 1
        else:
            return 'no_stop_a'
        return items[i]
    elif mode == 'b':
        return 'b'
    else:
        return 'c' """
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

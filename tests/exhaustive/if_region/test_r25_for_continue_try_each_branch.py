import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25ForContinueTryEachBranch(ExhaustiveTestCase):
    SOURCE_CODE = """def f(items, mode):
    if mode == 'a':
        for x in items:
            try:
                if x < 0:
                    continue
                process_a(x)
            except ValueError:
                pass
        return 'a_done'
    elif mode == 'b':
        for x in items:
            try:
                if x > 100:
                    continue
                process_b(x)
            except TypeError:
                pass
        return 'b_done'
    else:
        return 'c_done' """
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

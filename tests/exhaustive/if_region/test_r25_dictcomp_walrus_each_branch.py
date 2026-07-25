import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25DictcompWalrusEachBranch(ExhaustiveTestCase):
    SOURCE_CODE = """def f(flag, items):
    if flag == 'a':
        return {k: v for k, v in items if (n := v) > 0}
    elif flag == 'b':
        return {k: (n := v) for k, v in items if n > 0}
    else:
        return {k: v * 2 for k, v in items if (w := v) > 0}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

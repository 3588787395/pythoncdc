import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25StarredListLiteralEachBranch(ExhaustiveTestCase):
    SOURCE_CODE = """def f(flag, items):
    if flag == 'a':
        return [*items, 1, 2]
    elif flag == 'b':
        return [1, *items, 2]
    else:
        return [1, 2, *items]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

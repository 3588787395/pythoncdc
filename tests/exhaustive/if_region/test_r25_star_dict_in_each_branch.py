import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25StarDictInEachBranch(ExhaustiveTestCase):
    SOURCE_CODE = """def f(flag, extra):
    if flag == 'a':
        return {**extra, 'a': 1, 'b': 2}
    elif flag == 'b':
        return {'x': 1, **extra, 'y': 2}
    else:
        return {**extra, **{'z': 3}}"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

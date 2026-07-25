import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR25NestedWithTryInEachBranch(ExhaustiveTestCase):
    SOURCE_CODE = """def f(flag):
    if flag == 'a':
        return 'a'
    elif flag == 'b':
        with open('a') as fa, open('b') as fb:
            data = fa.read()
            with open('c') as fc:
                data += fc.read()
            return data + fb.read()
    else:
        return None"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()

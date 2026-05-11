import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN16Try_While_If_Break_a_IndexError(ExhaustiveTestCase):
    SOURCE_CODE = """def f(data, threshold):
    try:
        x = 0
        while x < len(data):
            if data[x] > threshold:
                break
            a = data[x]
            x += 1
    except IndexError:
        a = None"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()

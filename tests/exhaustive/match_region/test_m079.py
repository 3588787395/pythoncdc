import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM079(ExhaustiveTestCase):
    SOURCE_CODE = '''match x:
    case [a, b, c]:
        result = a + b + c
    case [a, b]:
        result = a + b
    case _:
        result = 0'''
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()

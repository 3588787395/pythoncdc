import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM084(ExhaustiveTestCase):
    SOURCE_CODE = '''match data:
    case ['add', x, y]:
        result = x + y
    case ['sub', x, y]:
        result = x - y
    case ['mul', x, y]:
        result = x * y
    case ['div', x, y] if y != 0:
        result = x / y
    case _:
        result = None
'''
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM083(ExhaustiveTestCase):
    SOURCE_CODE = '''match value:
    case int() as n if n > 0:
        result = f'positive integer: {n}'
    case int() as n if n < 0:
        result = f'negative integer: {n}'
    case str() as s if s:
        result = f'non-empty string: {s}'
    case list() as lst if len(lst) > 0:
        result = f'non-empty list: {len(lst)} items'
    case _:
        result = 'other'
'''
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()

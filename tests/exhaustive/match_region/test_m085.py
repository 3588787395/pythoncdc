import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM085(ExhaustiveTestCase):
    SOURCE_CODE = '''match nested:
    case {'items': [first, *rest]} if len(rest) > 0:
        total = first + sum(rest)
        count = 1 + len(rest)
    case {'items': [only]}:
        total = only
        count = 1
    case {'items': []}:
        total = 0
        count = 0
    case _:
        total = count = 0
'''
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()

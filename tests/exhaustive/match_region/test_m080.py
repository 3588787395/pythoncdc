import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM080(ExhaustiveTestCase):
    SOURCE_CODE = '''match x:
    case {'name': name, 'age': age} if age >= 18:
        status = 'adult'
    case {'name': name, 'age': age}:
        status = 'minor'
    case _:
        status = 'unknown'
'''
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestM082(ExhaustiveTestCase):
    SOURCE_CODE = '''match point:
    case (0, 0):
        quadrant = 'origin'
    case (x, 0) if x > 0:
        quadrant = 'positive x-axis'
    case (0, y) if y > 0:
        quadrant = 'positive y-axis'
    case (x, y) if x > 0 and y > 0:
        quadrant = 'first'
    case (x, y) if x < 0 and y > 0:
        quadrant = 'second'
    case (x, y) if x < 0 and y < 0:
        quadrant = 'third'
    case (x, y):
        quadrant = 'fourth'
'''
    REGION_TYPE = "MATCH"
    def test_decompile(self):
        self.verify_decompilation()

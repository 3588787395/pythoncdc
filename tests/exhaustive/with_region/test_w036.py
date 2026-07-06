import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW036(ExhaustiveTestCase):
    SOURCE_CODE = 'with ctx:\n    try:\n        x = 1\n    except TypeError:\n        y = 2\n    except ValueError:\n        z = 3'
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()

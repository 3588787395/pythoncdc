import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW042(ExhaustiveTestCase):
    SOURCE_CODE = 'with lock:\n    try:\n        x = critical_section()\n    except:\n        x = None'
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()

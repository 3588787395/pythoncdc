import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTernary20ComplexPractical(ExhaustiveTestCase):
    SOURCE_CODE = """def format_size(bytes_val):
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1048576:
        return f"{bytes_val/1024:.1f} KB" if bytes_val % 1024 == 0 else f"{bytes_val//1024} KB"
    else:
        return f"{bytes_val/1048576:.1f} MB" if bytes_val % 1048576 == 0 else f"{bytes_val//1048576} MB\""""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()

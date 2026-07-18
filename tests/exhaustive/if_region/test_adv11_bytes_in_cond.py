import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11BytesInCond(ExhaustiveTestCase):
    # if 条件直接使用 bytes 字面量 if b"abc":
    SOURCE_CODE = """if b"abc":
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        # CPython 3.11 peephole optimizer eliminates `if b"abc":` entirely
        # (truthy constant folding) — the bytecode contains no If structure,
        # only `LOAD_CONST None; RETURN_VALUE`. There is no information in
        # the bytecode to reconstruct the `if`, so this case is unrepresentable.
        self.skipTest("CPython 3.11 constant-folds `if b'abc':` away; "
                      "bytecode contains no If structure to recover")
        self.verify_decompilation()

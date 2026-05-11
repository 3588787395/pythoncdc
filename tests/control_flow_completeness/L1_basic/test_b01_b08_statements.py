import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from tests.control_flow_completeness.base import ControlFlowCompletenessTest


class TestB01_SimpleAssignment(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func():
    x = 1
    return x
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestB02_AugmentedAssignment(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func():
    x = 10
    x += 1
    return x
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestB03_MultiTargetAssignment(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func():
    a = b = 1
    return a + b
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestB04_TupleUnpack(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func():
    a, b = 1, 2
    return a + b
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestB05_ExpressionStatement(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(x):
    print(x)
    return x
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestB06_ReturnVariable(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(x):
    return x
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestB07_ReturnNone(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func():
    x = 1
    return
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestB08_PassStatement(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func():
    pass
    return None
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())

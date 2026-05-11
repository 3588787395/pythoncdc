import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from tests.control_flow_completeness.base import ControlFlowCompletenessTest


class TestC01_IfThen(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(x):
    if x > 0:
        x = x * 2
    return x
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestC02_IfElse(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(x):
    if x > 0:
        result = "positive"
    else:
        result = "non-positive"
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestC03_IfElif(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(x):
    if x > 0:
        result = "positive"
    elif x < 0:
        result = "negative"
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestC04_IfElifElse(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(x):
    if x > 0:
        result = "positive"
    elif x < 0:
        result = "negative"
    else:
        result = "zero"
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestC05_MultiElifChain(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(score):
    if score >= 90:
        grade = 'A'
    elif score >= 80:
        grade = 'B'
    elif score >= 70:
        grade = 'C'
    elif score >= 60:
        grade = 'D'
    else:
        grade = 'F'
    return grade
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestC06_NestedIf(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(x, y):
    if x > 0:
        if y > 0:
            result = "both positive"
        else:
            result = "x positive only"
    else:
        result = "x non-positive"
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestC07_NestedIfElse(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(a, b, c):
    if a:
        if b:
            if c:
                result = 1
            else:
                result = 2
        else:
            result = 3
    else:
        result = 4
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())

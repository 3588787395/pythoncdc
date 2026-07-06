import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from tests.control_flow_completeness.base import ControlFlowCompletenessTest


# If内嵌套 (CF1, CF2, CE1, CW1, CI1)

class TestCF1_IfWithFor(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(flag, items):
    result = []
    if flag:
        for item in items:
            result.append(item * 2)
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestCF2_IfWithWhile(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(flag, n):
    result = []
    if flag:
        i = 0
        while i < n:
            result.append(i)
            i += 1
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestCE1_IfWithTry(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(flag, data):
    result = None
    if flag:
        try:
            result = int(data)
        except ValueError:
            result = 0
    else:
        result = -1
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestCW1_IfWithWith(ControlFlowCompletenessTest):
    SOURCE_CODE = """
from io import StringIO

def test_func(flag, text):
    content = ""
    if flag:
        with StringIO(text) as f:
            content = f.read()
    return content
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestCI1_DeepNestedIf(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(a, b, c, d):
    if a:
        if b:
            if c:
                result = d * 2
            else:
                result = d
        else:
            result = 0
    else:
        result = -1
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


# For内嵌套 (FC1, FF1, FT1, FW1, FB1)

class TestFC1_ForWithIf(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(items):
    result = []
    for item in items:
        if item > 0:
            result.append(item)
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestFF1_ForWithFor(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(matrix):
    flat = []
    for row in matrix:
        for val in row:
            flat.append(val)
    return flat
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestFT1_ForWithTry(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(strings):
    results = []
    for s in strings:
        try:
            val = int(s)
        except ValueError:
            val = None
        results.append(val)
    return results
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestFW1_ForWithWith(ControlFlowCompletenessTest):
    SOURCE_CODE = """
from io import StringIO

def test_func(texts):
    contents = []
    for text in texts:
        with StringIO(text) as f:
            contents.append(f.read())
    return contents
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestFB1_ForIfBreakContinue(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(items):
    positives = []
    negatives = []
    for item in items:
        if item > 0:
            positives.append(item)
            continue
        negatives.append(abs(item))
    return positives, negatives
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


# While内嵌套 (WC1, WF1, WT1, WW1, WB1)

class TestWC1_WhileWithIf(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(limit):
    evens = []
    i = 0
    while i < limit:
        if i % 2 == 0:
            evens.append(i)
        i += 1
    return evens
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestWF1_WhileWithFor(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(groups):
    all_items = []
    idx = 0
    while idx < len(groups):
        for item in groups[idx]:
            all_items.append(item)
        idx += 1
    return all_items
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestWT1_WhileWithTry(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(n):
    results = []
    i = 0
    while i < n:
        try:
            val = 10 / i
        except ZeroDivisionError:
            val = float('inf')
        results.append(val)
        i += 1
    return results
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestWW1_WhileWithWith(ControlFlowCompletenessTest):
    SOURCE_CODE = """
from io import StringIO

def test_func(texts):
    contents = []
    idx = 0
    while idx < len(texts):
        with StringIO(texts[idx]) as f:
            contents.append(f.read())
        idx += 1
    return contents
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestWB1_WhileIfBreakContinue(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(n):
    sum_pos = 0
    count_neg = 0
    i = 0
    while i < n:
        i += 1
        if i % 2 == 0:
            continue
        if i > n // 2:
            break
        sum_pos += i
        count_neg += 1
    return sum_pos, count_neg
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


# Try内嵌套 (TF1, TW1, TI1, TT1)

class TestTF1_TryWithFor(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(items):
    result = []
    try:
        for item in items:
            result.append(item * 2)
    except Exception:
        result = []
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestTW1_TryWithWith(ControlFlowCompletenessTest):
    SOURCE_CODE = """
from io import StringIO

def test_func(text):
    content = ""
    try:
        with StringIO(text) as f:
            content = f.read()
    except IOError:
        content = "error"
    return content
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestTI1_TryWithIf(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(x, y):
    result = 0
    try:
        if y != 0:
            result = x / y
        else:
            result = 0
    except Exception:
        result = -1
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestTT1_TryWithTry(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func():
    result = None
    try:
        try:
            inner = risky_op()
        except ValueError:
            inner = "value error"
    except Exception:
        outer = "outer error"
    else:
        result = inner
    return result

def risky_op():
    return 42
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


# With内嵌套 (WF2, WI2, WT2, WW2)

class TestWF2_WithFor(ControlFlowCompletenessTest):
    SOURCE_CODE = """from io import StringIO

def test_func(texts):
    contents = []
    with StringIO("") as log:
        for text in texts:
            with StringIO(text) as f:
                contents.append(f.read())
                log.write("processed\\n")
    return contents
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestWI2_WithIf(ControlFlowCompletenessTest):
    SOURCE_CODE = """
from io import StringIO

def test_func(flag, text):
    content = ""
    with StringIO(text) as f:
        if flag:
            content = f.read()
        else:
            content = "skipped"
    return content
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestWT2_WithTry(ControlFlowCompletenessTest):
    SOURCE_CODE = """
from io import StringIO

def test_func(text):
    content = ""
    with StringIO(text) as f:
        try:
            content = f.read()
        except IOError:
            content = "error"
    return content
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestWW2_NestedWith(ControlFlowCompletenessTest):
    SOURCE_CODE = """
from io import StringIO

def test_func(t1, t2):
    combined = ""
    with StringIO(t1) as f1:
        with StringIO(t2) as f2:
            combined = f1.read() + f2.read()
    return combined
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


# Break/Continue语义验证 (BC1-BC7)

class TestBC1_ForBreak(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(items, target):
    found_index = -1
    for i, item in enumerate(items):
        if item == target:
            found_index = i
            break
    return found_index
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestBC2_ForContinue(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(items):
    filtered = []
    for item in items:
        if item is None:
            continue
        filtered.append(str(item))
    return filtered
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestBC3_IfElseBreakInThen(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(items, target):
    status = "not found"
    for item in items:
        if item == target:
            status = "found"
            break
        else:
            status = "checking next"
    return status
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestBC4_WhileBreak(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(start, limit):
    current = start
    while True:
        if current >= limit:
            break
        current += 1
    return current
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestBC5_NestedForInnerBreak(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(matrix, target):
    position = None
    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            if val == target:
                position = (i, j)
                break
        if position:
            break
    return position
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestBC6_NestedForInnerContinue(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(matrix):
    first_elements = []
    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            if j != 0:
                continue
            first_elements.append((i, val))
    return first_elements
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestBC7_ForBreakElse(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(items, target):
    found = False
    for item in items:
        if item == target:
            found = True
            break
    else:
        found = False
    return found
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())

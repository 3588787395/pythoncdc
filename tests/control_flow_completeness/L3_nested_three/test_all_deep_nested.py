import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from tests.control_flow_completeness.base import ControlFlowCompletenessTest


# N01-N04: For > 条件 > 跳转

class TestN01_ForIfBreak(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(items, threshold):
    result = []
    for item in items:
        if item > threshold:
            break
        result.append(item)
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestN02_ForIfContinue(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(items):
    result = []
    for item in items:
        if item <= 0:
            continue
        result.append(item * 2)
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestN03_ForForIfBreak(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(matrix, target):
    pos = None
    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            if val == target:
                pos = (i, j)
                break
        if pos:
            break
    return pos
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestN04_ForForIfContinue(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(matrix):
    diagonals = []
    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            if i != j:
                continue
            diagonals.append(val)
    return diagonals
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


# N05-N09: While > 条件 > 跳转

class TestN05_WhileIfBreak(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(max_val, threshold):
    values = []
    current = 0
    while True:
        if current >= max_val:
            break
        if current > threshold:
            break
        values.append(current)
        current += 1
    return values
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestN06_WhileIfContinue(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(n):
    odds = []
    i = 0
    while i < n:
        i += 1
        if i % 2 == 0:
            continue
        odds.append(i)
    return odds
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestN07_WhileForIfBreak(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(groups, target):
    found_at = None
    g_idx = 0
    while g_idx < len(groups):
        for item in groups[g_idx]:
            if item == target:
                found_at = (g_idx, item)
                break
        if found_at:
            break
        g_idx += 1
    return found_at
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestN08_WhileForIfContinue(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(groups):
    first_items = []
    g_idx = 0
    while g_idx < len(groups):
        for i, item in enumerate(groups[g_idx]):
            if i != 0:
                continue
            first_items.append(item)
        g_idx += 1
    return first_items
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestN09_WhileWhileIfBreak(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(grid, target):
    pos = None
    i = 0
    while i < len(grid):
        j = 0
        while j < len(grid[i]):
            if grid[i][j] == target:
                pos = (i, j)
                break
            j += 1
        if pos:
            break
        i += 1
    return pos
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


# N10-N13: 外层结构变体

class TestN10_TryForIfExcept(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(items, threshold):
    result = []
    try:
        for item in items:
            if item > threshold:
                raise ValueError("too large")
            result.append(item)
    except ValueError:
        result = []
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestN11_TryWhileIfExcept(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(limit, threshold):
    values = []
    try:
        i = 0
        while i < limit:
            if i > threshold:
                raise StopIteration("threshold exceeded")
            values.append(i)
            i += 1
    except StopIteration:
        values = [-1]
    return values
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestN12_ForTryIfExcept(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(strings):
    converted = []
    for s in strings:
        try:
            if not s:
                raise ValueError("empty string")
            val = int(s)
        except ValueError:
            val = 0
        converted.append(val)
    return converted
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestN13_WhileTryIfExcept(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(n):
    results = []
    i = 0
    while i < n:
        try:
            if i == 0:
                raise ZeroDivisionError("first iteration")
            val = 100 / i
        except ZeroDivisionError:
            val = 0
        results.append(val)
        i += 1
    return results
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


# N14-N18: 混合三层嵌套

class TestN14_ForIfForIfBreak(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(matrix, target):
    pos = None
    for i, row in enumerate(matrix):
        if any(x == target for x in row):
            for j, val in enumerate(row):
                if val == target:
                    pos = (i, j)
                    break
            if pos:
                break
    return pos
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestN15_WhileIfWhileIfBreak(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(grids, target):
    pos = None
    gi = 0
    while gi < len(grids):
        grid = grids[gi]
        if any(target in row for row in grid):
            gj = 0
            while gj < len(grid):
                row = grid[gj]
                ri = 0
                while ri < len(row):
                    if row[ri] == target:
                        pos = (gi, gj, ri)
                        break
                    ri += 1
                if pos:
                    break
                gj += 1
        if pos:
            break
        gi += 1
    return pos
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestN16_ForForIfBreak(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(cubes, target):
    coords = None
    for i, matrix in enumerate(cubes):
        for j, row in enumerate(matrix):
            if target in row:
                coords = (i, j)
                break
        if coords:
            break
    return coords
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestN17_ForTryIfExcept(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(rows):
    processed = []
    for i, row_data in enumerate(rows):
        try:
            if len(row_data) == 0:
                raise ValueError("empty row")
            total = sum(row_data)
        except ValueError:
            total = 0
        processed.append(total)
    return processed
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestN18_TryForIfTryExcept(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(data_groups):
    all_results = []
    try:
        for group in data_groups:
            group_results = []
            for value in group:
                try:
                    if value < 0:
                        raise ValueError("negative")
                    parsed = str(value)
                except ValueError:
                    parsed = "NEG"
                group_results.append(parsed)
            all_results.append(group_results)
    except Exception:
        all_results = [["ERROR"]]
    return all_results
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())

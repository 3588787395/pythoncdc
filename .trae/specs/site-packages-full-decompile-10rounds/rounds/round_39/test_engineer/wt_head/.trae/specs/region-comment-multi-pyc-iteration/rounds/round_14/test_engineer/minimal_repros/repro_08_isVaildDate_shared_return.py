"""R14 CTRL 08: isVaildDate shared trailing return after if/elif/else in try body.

CTRL (NO-DEFECT after R14 fix): mirrors tools.pyc isVaildDate. Before the R14
fix the shared `return True` (block 182) was incorrectly placed inside the
first if-branch. The R14 fix (shared merge_block detection in
region_ast_generator._generate_if) emits it as a post-if trailing statement.
This repro verifies the fix: decompile -> recompile must match bytecode.
"""
import time


def isVaildDate(date):
    try:
        if '-' in date:
            if len(date) != 10:
                return False
            else:
                time.strptime(date, '%Y-%m-%d')
        elif len(date) != 8:
            return False
        else:
            time.strptime(date, '%Y%m%d')
        return True
    except BaseException:
        return False

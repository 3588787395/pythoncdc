# Pattern: module-level 2 function definitions + import (mirror <module>)
# Function: mirror common.pyc <module> structure
# Expected: import + 2 def at module level
# Actual: same (pyc 100% match, NO-DEFECT control)
import datetime
def fn_a(x):
    return x + 1
def fn_b(y):
    return y - 1
# NO-DEFECT

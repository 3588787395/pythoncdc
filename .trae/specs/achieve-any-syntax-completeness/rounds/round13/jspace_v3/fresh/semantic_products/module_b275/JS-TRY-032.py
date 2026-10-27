# Source Generated with Decompyle++ (Python version)
# File: m04_module_try.pyc (Python 3.11)

"""m04: module-level try hosts with deep nesting."""
import json
class _CM:
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        return False
try:
    CFG = json
except ImportError:
    CFG = None
else:
    HOOK = CFG
finally:
    TAG = 't'
try:
    try:
        for i in range(2):
            with _CM() as j:
                if i:
                    while i:
                        i -= 1
    except ValueError:
        CFG = 1
    finally:
        DONE = 1
except NameError:
    DONE = 2

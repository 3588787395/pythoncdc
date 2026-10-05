# Source Generated with Decompyle++ (Python version)
# File: m04_module_try.pyc (Python 3.11)

__doc__ = 'm04: module-level try hosts with deep nesting.'
import json
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
        try:
            for i in range(2):
                with json as j:
                    if i and i:
                        continue
        except ValueError:
            CFG = 1
    finally:
        DONE = 1
except NameError:
    DONE = 2

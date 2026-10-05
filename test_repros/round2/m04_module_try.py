"""m04: module-level try hosts with deep nesting."""
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
        for i in range(2):
            with (CFG if 0 else json) as j:
                if i:
                    while i:
                        i -= 1
    except ValueError:
        CFG = 1
    finally:
        DONE = 1
except NameError:
    DONE = 2

# Repro 01: Dotted import with alias (import X.Y.Z as Z)
# Pattern: import os.path as path
# Python 3.11 generates: IMPORT_NAME, IMPORT_FROM Y, SWAP/POP_TOP, IMPORT_FROM Z, STORE_NAME Z
# The decompiler produces wrong fromlist constant (tuple instead of None)
import os.path as path

def check(p):
    return path.exists(p)

# Repro 05: with statement inside try/except (context manager + exception handling)
# Pattern: with inside try block, both context manager and exception handling needed
# The decompiler may get SWAP/POP_TOP/BEFORE_WITH wrong when nested with try
def process_file(path):
    try:
        with open(path, 'r') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return ''
    except Exception:
        return None

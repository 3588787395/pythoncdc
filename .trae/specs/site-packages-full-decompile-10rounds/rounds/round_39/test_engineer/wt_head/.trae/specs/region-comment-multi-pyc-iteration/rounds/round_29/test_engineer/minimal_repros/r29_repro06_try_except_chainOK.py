# Source Generated with Decompyle++ (Python version)
# File: r29_repro06_try_except_chain.cpython-311.pyc (Python 3.11)

def func_try_except_chain():
    try:
        try:
            pass
        except:
            pass
        import json
    except:
        pass
    else:
        return json.dumps({'a': 1})

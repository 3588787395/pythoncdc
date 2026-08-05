
def func_try_except_empty():
    try:
        import json
    except:
        pass
    try:
        import os
    except:
        pass
    return json.dumps({"a": 1})

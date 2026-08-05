
def func_try_except_chain():
    try:
        import json
    except:
        pass
    try:
        import os
    except:
        pass
    return json.dumps({"a": 1})

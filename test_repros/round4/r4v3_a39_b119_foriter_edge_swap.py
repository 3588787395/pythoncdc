def a39(x):
    if isinstance(x, str):
        return 1
    elif isinstance(x, list):
        for i in x:
            return 2

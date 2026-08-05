
def func_for_else_with_calls():
    for item in [1, 2, 3]:
        if item == 2:
            return "found"
    else:
        print("not found")
        return "not found"
    return "unreachable"

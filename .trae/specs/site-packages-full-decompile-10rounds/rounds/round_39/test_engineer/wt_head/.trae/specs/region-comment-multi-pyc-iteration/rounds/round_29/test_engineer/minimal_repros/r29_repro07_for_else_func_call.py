
def func_for_else_func_call():
    args = ["a", "b"]
    for arg in args:
        if arg == "b":
            return "found_b"
    else:
        print("conversion done")
        return "not_found"

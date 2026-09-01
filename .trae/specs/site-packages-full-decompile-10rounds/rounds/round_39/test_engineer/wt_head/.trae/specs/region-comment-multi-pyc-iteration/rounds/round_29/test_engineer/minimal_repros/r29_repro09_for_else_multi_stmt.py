
def func_for_else_multi_stmt():
    items = [1, 2, 3]
    for item in items:
        if item == 5:
            return "found"
    else:
        total = sum(items)
        print(f"Total: {total}")
        return total

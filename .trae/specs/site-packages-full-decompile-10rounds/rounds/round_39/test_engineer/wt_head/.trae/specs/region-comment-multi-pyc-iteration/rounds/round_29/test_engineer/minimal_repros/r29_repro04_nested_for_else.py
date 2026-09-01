
def func_nested_for_else():
    for i in range(3):
        for j in range(3):
            if i + j == 4:
                return i, j
    else:
        return None

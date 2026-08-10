# for-else with break
def test():
    for item in [1, 2, 3]:
        if item == 2:
            break
    else:
        print("not found")
    return "done"

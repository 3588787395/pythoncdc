# Repro 08: for loop with break and else clause
# Pattern: for...else with break - when break is hit, else is skipped
# Decompiler may emit JUMP_FORWARD instead of JUMP_BACKWARD for loop iteration
def find_target(items, target):
    for i, item in enumerate(items):
        if item == target:
            break
    else:
        return -1
    return i

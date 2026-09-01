# R101-Pattern-B: for + if{nested-if, continue} + assign + break (get_str_data)
# The `continue` guards trailing loop-body statements.


def scan(flags):
    found = -1
    for j in range(len(flags)):
        if flags[j] == 1:
            if j == len(flags) - 1:
                found = -2
            continue
        found = j
        break
    return found


def run(flags):
    return scan(flags)

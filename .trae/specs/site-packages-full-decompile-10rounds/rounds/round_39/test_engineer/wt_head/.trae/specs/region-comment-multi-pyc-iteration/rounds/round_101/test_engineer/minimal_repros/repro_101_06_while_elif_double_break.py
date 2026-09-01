# R101-Pattern-C: while + elif branch with DOUBLE break (change_his_to_backward)
# Original source contains two consecutive `break` statements; the second is
# unreachable but present in original bytecode as a second JUMP_BACKWARD.


def drain(keys, empty_at):
    out = []
    i = 0
    while i < len(keys):
        if keys[i] == 'stop':
            break
        elif i == empty_at:
            break
            break
        else:
            out.append(keys[i])
        i += 1
    return out


def run(keys, e):
    return drain(keys, e)

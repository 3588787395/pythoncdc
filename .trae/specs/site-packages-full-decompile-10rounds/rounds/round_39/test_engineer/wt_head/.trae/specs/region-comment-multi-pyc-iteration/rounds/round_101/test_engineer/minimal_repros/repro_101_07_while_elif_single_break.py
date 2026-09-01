# R101-Pattern-C-control: while + elif with SINGLE break (healthy baseline
# for the double-break repro 06).


def drain(keys):
    out = []
    i = 0
    while i < len(keys):
        if keys[i] == 'stop':
            break
        elif i == 1:
            break
        else:
            out.append(keys[i])
        i += 1
    return out


def run(keys):
    return drain(keys)

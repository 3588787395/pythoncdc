D = {}
C = 1


def probe_a(items, op_station):
    out = []
    for item in items:
        if item['s'] != '2' and (not op_station or item['o'] == op_station):
            if item['t'] in list(D.values()):
                out.append(item)
    return out


def probe_b(items, op_station, flag):
    out = []
    for item in items:
        if flag:
            if item['s'] != '2' and (not op_station or item['o'] == op_station):
                if item['t'] in list(D.values()):
                    out.append(item)
                continue
            elif item['s'] != '2' and (not op_station or item['o'] == op_station):
                if item['t'] == C:
                    out.append(item)
                continue
        else:
            out.append(item)
    return out

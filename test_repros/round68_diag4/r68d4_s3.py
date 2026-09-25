import os
D = {}
C = 1
LOCAL = 1


def w1(rd, st, mode, op_station, trades):
    try:
        for item in rd:
            if st is None:
                if mode == 'c':
                    if item['s'] != '2' and (not op_station or item['o'] == op_station):
                        if item['t'] in list(D.values()):
                            trades.append(item)
                else:
                    if item['s'] != '2' and (not op_station or item['o'] == op_station):
                        if item['t'] == C:
                            trades.append(item)
            elif st == 'trade':
                if item['s'] in ('0', '5'):
                    trades.append(item)
    except Exception:
        pass


def w2(rd, st, mode, op_station, trades):
    try:
        for item in rd:
            if st is None:
                if mode == 'c':
                    if item['s'] != '2' and (not op_station or item['o'] == op_station):
                        if item['t'] in list(D.values()):
                            trades.append(item)
    except Exception:
        pass


def w3(rd, st, mode, op_station, trades):
    if os.path.exists('f'):
        for item in rd:
            if st is None:
                if mode == 'c':
                    if item['s'] != '2' and (not op_station or item['o'] == op_station):
                        if item['t'] in list(D.values()):
                            trades.append(item)
    for item in rd:
        if item['s'] in ('0', '5') and item['k'] == LOCAL:
            trades.append(item)


def w4(rd, st, mode, op_station, trades):
    for item in rd:
        if st is None:
            if mode == 'c':
                if item['s'] != '2' and (not op_station or item['o'] == op_station):
                    if item['t'] in list(D.values()):
                        trades.append(item)
                    continue
            elif item['s'] != '2' and (not op_station or item['o'] == op_station):
                if item['t'] == C:
                    trades.append(item)
                continue
            elif item['s'] in ('0', '5') and item['p'] == LOCAL:
                if item['t'] in list(D.values()):
                    trades.append(item)
                continue
        elif item['s'] in ('0', '5') and item['q'] == LOCAL:
            if item['t'] == C:
                trades.append(item)
            continue

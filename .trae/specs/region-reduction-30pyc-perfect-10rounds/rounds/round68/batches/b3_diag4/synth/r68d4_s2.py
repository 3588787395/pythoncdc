D = {}
C = 1
LOCAL = 1


def v1(rd, st, mode, op_station, trades):
    for item in rd:
        if st is None:
            if mode == 'c':
                if item['s'] != '2' and (not op_station or item['o'] == op_station):
                    if item['t'] in list(D.values()):
                        trades.append(item)


def v2(rd, st, mode, op_station, trades):
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


def v3(rd, st, mode, op_station, trades):
    for item in rd:
        if st is None:
            if mode == 'c':
                if item['s'] != '2' and (not op_station or item['o'] == op_station):
                    if item['t'] in list(D.values()):
                        trades.append(item)
            elif item['s'] != '2' and (not op_station or item['o'] == op_station):
                if item['t'] == C:
                    trades.append(item)
        elif st == 'trade':
            if item['s'] in ('0', '5'):
                trades.append(item)


def v4(rd, mode, op_station, trades):
    for item in rd:
        if mode == 'c':
            if item['s'] != '2' and (not op_station or item['o'] == op_station):
                if item['t'] in list(D.values()):
                    trades.append(item)


def v5(rd, st, mode, op_station, trades):
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
        elif st == 'trade':
            if item['s'] in ('0', '5'):
                trades.append(item)
                continue
        elif item['s'] in ('0', '5') and item['x'] == LOCAL:
            trades.append(item)


def v6(rd, st, mode, op_station, trades):
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
        elif st == 'x':
            if item['s'] in ('0', '5'):
                trades.append(item)
        elif item['s'] in ('0', '5') and item['y'] == LOCAL:
            trades.append(item)

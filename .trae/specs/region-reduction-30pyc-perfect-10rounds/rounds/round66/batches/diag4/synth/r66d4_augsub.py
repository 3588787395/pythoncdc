def probe(s, info, sv):
    for k in info:
        a = sv.get(k, 0)
        b = info.get(k, 0)
        if a == 0:
            break
        elif a > b:
            s['win'] += 1
            s['profit'] += a - b
            s['tot'] += 1
            continue
        else:
            s['lost'] += 1
            s['loss'] += a - b
            s['tot'] += 1
            continue

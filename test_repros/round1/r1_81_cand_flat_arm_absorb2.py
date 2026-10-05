def f81(p):
    info = {}
    if p != '':
        if p == '1':
            info['x'] = 'no'
            return info
        else:
            info['y'] = 1
            if p == '2':
                info['z'] = 2
                return info
            print('inner')
    print('after-if')
    info['n'] = 0
    return info

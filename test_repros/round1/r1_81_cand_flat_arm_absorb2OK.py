# Source Generated with Decompyle++ (Python version)
# File: r1_81_cand_flat_arm_absorb2.pyc (Python 3.11)

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
            else:
                print('inner')
    print('after-if')
    info['n'] = 0
    return info

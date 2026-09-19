# Source Generated with Decompyle++ (Python version)
# File: r3_03b_while_cond_probe.pyc (Python 3.11)

__doc__ = 'R3-L 触发条件探针: while 条件中 not X and Y vs X is None and Y vs X == 0 and Y。'
def p_not(self):
    redata, count = None, 0
    while not redata and count < 3:
        redata = self.fetch()
        count += 1
    return redata
def p_isnone(self):
    redata, count = None, 0
    while redata is None and count < 3:
        redata = self.fetch()
        count += 1
    return redata
def p_eq(self):
    redata, count = 0, 0
    while redata == 0 and count < 3:
        redata = self.fetch()
        count += 1
    return redata
def p_not_noand(self):
    redata, count = None, 0
    while not redata:
        redata = self.fetch()
        count += 1
    return redata

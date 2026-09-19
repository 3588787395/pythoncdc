# Source Generated with Decompyle++ (Python version)
# File: r3_03d_while_sleep_probe.pyc (Python 3.11)

__doc__ = 'R3-L 精化探针2: while not redata and count < 3: 循环体首条语句为方法调用 (time.sleep 形态)。'
def p_sleep_first(self):
    redata, flag, count = None, 0, 0
    while not redata and count < 3:
        self.sleep(3)
        if flag == 1:
            self.warn('a')
        elif flag == -1:
            self.warn('b')
        redata, flag = self.fetch()
        count += 1
    return redata
def p_sleep_mid(self):
    redata, flag, count = None, 0, 0
    while not redata and count < 3:
        if flag == 1:
            self.warn('a')
        elif flag == -1:
            self.warn('b')
        self.sleep(3)
        redata, flag = self.fetch()
        count += 1
    return redata

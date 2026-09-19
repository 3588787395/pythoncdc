"""R3-L 精化探针: while not redata and count < 3: 循环体内容 —— 元组解包 vs if/elif。"""


def p_tuple(self):
    redata, flag, count = None, 0, 0
    while not redata and count < 3:
        redata, flag = self.fetch()
        count += 1
    return redata


def p_elif(self):
    redata, flag, count = None, 0, 0
    while not redata and count < 3:
        if flag == 1:
            self.warn('a')
        elif flag == -1:
            self.warn('b')
        redata = self.fetch()
        count += 1
    return redata


def p_both(self):
    redata, flag, count = None, 0, 0
    while not redata and count < 3:
        if flag == 1:
            self.warn('a')
        elif flag == -1:
            self.warn('b')
        redata, flag = self.fetch()
        count += 1
    return redata

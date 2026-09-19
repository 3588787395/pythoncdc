def f(self):
    op = self.get_argument('a', False) or self.get_argument('b', '')
    if self.flag:
        return 1
    else:
        return 2

def f(self):
    self.op = self.get_argument('a', False) or self.get_argument('b', '')
    user = self.get_current_user()
    if user is None:
        return 1
    else:
        return 2

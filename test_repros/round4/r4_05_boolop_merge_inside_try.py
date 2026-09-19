def f(self):
    op = self.get_argument('a', False) or self.get_argument('b', '')
    user = self.get_current_user()
    try:
        self.foo(user)
    except Exception:
        pass
    return op

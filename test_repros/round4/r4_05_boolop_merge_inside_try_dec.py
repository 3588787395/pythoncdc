# Source Generated with Decompyle++ (Python version)
# File: r4_05_boolop_merge_inside_try.pyc (Python 3.11)

def f(self):
    op = self.get_argument('a', False) or self.get_argument('b', '')
    user = self.get_current_user()
    try:
        self.foo(user)
    except Exception:
        pass
    return op

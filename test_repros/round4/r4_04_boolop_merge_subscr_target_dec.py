# Source Generated with Decompyle++ (Python version)
# File: r4_04_boolop_merge_subscr_target.pyc (Python 3.11)

def f(self):
    d = {}
    d['k'] = self.get_argument('a', False) or self.get_argument('b', '')
    user = self.get_current_user()
    if user is None:
        return 1
    else:
        return 2

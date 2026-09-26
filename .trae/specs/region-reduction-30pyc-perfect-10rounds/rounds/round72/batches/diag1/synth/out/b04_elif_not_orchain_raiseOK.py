# Source Generated with Decompyle++ (Python version)
# File: b04_elif_not_orchain_raise.pyc (Python 3.11)

class Cache:
    def __init__(self):
        self._Cache__future_info = {}
        self._Cache__user_info = {}
    def info_conbine(self, username, future_code):
        if future_code not in self._Cache__future_info:
            raise Exception('No such future_code')
        elif not (username not in self._Cache__user_info or self._Cache__user_info[username]):
            raise Exception('Current user is not available')
        elif future_code not in self._Cache__user_info[username]:
            raise Exception('This future_code is not available for current user')
        else:
            future_info = self._Cache__future_info[future_code].copy()
            future_info.update(self._Cache__user_info[username][future_code])
            return future_info

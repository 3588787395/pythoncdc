# F-ORELSE/F-BOOLOP (future_contract_info info_conbine): elif arm whose guard is
# `A or not B`. Decompiler re-emits the arm as `elif not (A or B): ...` (De Morgan
# applied to the wrong node), flipping the arm's jump: A@66 -> 94 vs B@66 -> 124.
class Cache:
    def __init__(self):
        self.__future_info = {}
        self.__user_info = {}

    def info_conbine(self, username, future_code):
        if future_code not in self.__future_info:
            raise Exception('No such future_code')
        elif username not in self.__user_info or not self.__user_info[username]:
            raise Exception('Current user is not available')
        elif future_code not in self.__user_info[username]:
            raise Exception('This future_code is not available for current user')
        else:
            future_info = self.__future_info[future_code].copy()
            future_info.update(self.__user_info[username][future_code])
            return future_info

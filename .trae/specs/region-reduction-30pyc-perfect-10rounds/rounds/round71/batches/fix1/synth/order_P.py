class OrderStatus:
    CANCELLED = 2


class _Log:
    def warning(self, *a, **k):
        pass


user_log = _Log()


class Order:
    def is_final(self):
        return False

    def mark_cancelled(self, cancelled_reason, user_warn=True):
        if not self.is_final():
            self._message = cancelled_reason
            self._status = OrderStatus.CANCELLED
            if user_warn:
                user_log.warning(cancelled_reason)
                return None
                return None
            else:
                return None

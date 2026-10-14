# Source Generated with Decompyle++ (Python version)
# File: r9w16_10_class_method_ctx.pyc (Python 3.11)

class R9W16Ten(object):
    def _trade_status_handle(self, orders):
        while True:
            if len(self.open_orders) > 0:
                order = self.open_orders.pop(0)
                self.send(order)
            sleep(0.5)

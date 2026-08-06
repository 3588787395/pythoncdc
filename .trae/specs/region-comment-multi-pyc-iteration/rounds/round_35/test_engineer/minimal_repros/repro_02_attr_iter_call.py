"""R35 最小复现实例 2: 推导式属性访问误判为方法调用"""
# 原始: [order for order in self.orders if not order.is_final()]
# 反编译: [order for order in self.orders() if not order.is_final()]
# 根因: _generate_return_ast 跳过 CALL 指令

class TestClass:
    def __init__(self):
        self.orders = []

    def get_open_orders(self, symbol=None):
        if symbol is None:
            return [order for order in self.orders if not order.is_final()]
        else:
            return [order for order in self.orders if order.symbol == symbol]

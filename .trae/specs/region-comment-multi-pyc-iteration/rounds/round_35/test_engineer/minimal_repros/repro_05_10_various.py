"""R35 最小复现实例 5-10: 各种控制流模式"""
# 5: for 循环中的属性迭代
class Test5:
    def method(self):
        for item in self.items:
            if item.value > 0:
                return item
        return None

# 6: try-except 中的属性访问
class Test6:
    def method(self):
        try:
            return self.data.value
        except AttributeError:
            return None

# 7: 嵌套 if 中的方法调用
class Test7:
    def method(self, x):
        if x is not None:
            if x.is_valid():
                return x.process()
        return None

# 8: while 循环中的条件
class Test8:
    def method(self):
        while self.running:
            if self.check():
                break
        return self.result

# 9: 推导式中的方法调用（正确模式）
class Test9:
    def method(self):
        return [x for x in self.get_items() if x.is_valid()]

# 10: 多重推导式
class Test10:
    def method(self):
        return {k: v for k, v in self.items.items() if v is not None}

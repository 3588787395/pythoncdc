# 复杂类定义测试
class ComplexClass:
    """这是一个复杂的类，包含多种方法类型"""
    
    class_var = 100
    
    def __init__(self, value):
        self.value = value
        self._private = 0
    
    @property
    def private(self):
        return self._private
    
    @private.setter
    def private(self, val):
        self._private = val
    
    @classmethod
    def create_default(cls):
        return cls(0)
    
    @staticmethod
    def utility_function(x):
        return x * 2
    
    def instance_method(self):
        return self.value + self.class_var
    
    def __str__(self):
        return f"ComplexClass({self.value})"

# 复杂装饰器测试
def decorator_with_args(arg1, arg2):
    def actual_decorator(func):
        def wrapper(*args, **kwargs):
            print(f"Decorator args: {arg1}, {arg2}")
            return func(*args, **kwargs)
        return wrapper
    return actual_decorator

@decorator_with_args("hello", 42)
def my_function(x):
    return x * 2

# 多个装饰器
@decorator_with_args("a", 1)
@decorator_with_args("b", 2)
def multi_decorated():
    return "done"

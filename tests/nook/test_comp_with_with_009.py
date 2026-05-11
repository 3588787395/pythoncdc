# with语句中的推导式测试
# 测试上下文管理器中的推导
from contextlib import contextmanager

@contextmanager
def managed_resource():
    data = [1, 2, 3, 4, 5]
    try:
        yield data
    finally:
        pass

with managed_resource() as data:
    result = [x**2 for x in data]

# 带异常的上下文管理器测试
class SafeContext:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            print(f"Handling exception: {exc_val}")
        return True

with SafeContext():
    raise ValueError("Test error")

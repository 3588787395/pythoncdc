#!/usr/bin/env python3
def safe_execute(func, *args, default=None, **kwargs):
    """安全执行函数"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"Error executing {func.__name__}: {e}")
        return default

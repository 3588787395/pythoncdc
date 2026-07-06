#!/usr/bin/env python3
"""
测试f-string格式化问题 - 从quote.pyc提取

原始代码中的问题:
```python
temp_time = f"{v[0:4]2}-{v[4:6]2}-{v[6:8]2} {'00'2}:{'00'2}:{'00'2}"
```

正确代码应该是:
```python
temp_time = f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[8:10]}:{v[10:12]}:{v[12:14]}"
```
"""

def format_time_v1(v):
    """版本1: 简单的f-string格式化"""
    temp_time = f"{v[0:4]}-{v[4:6]}-{v[6:8]}"
    return temp_time

def format_time_v2(v):
    """版本2: 带时间部分的f-string格式化"""
    temp_time = f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[8:10]}:{v[10:12]}:{v[12:14]}"
    return temp_time

def format_time_v3(v):
    """版本3: 条件f-string格式化"""
    if len(v) == 8:
        temp_time = f"{v[0:4]}-{v[4:6]}-{v[6:8]} 00:00:00"
    elif len(v) == 12:
        temp_time = f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[8:10]}:{v[10:12]}:00"
    elif len(v) == 14:
        temp_time = f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[8:10]}:{v[10:12]}:{v[12:14]}"
    else:
        temp_time = v
    return temp_time

def format_with_padding(v):
    """版本4: 带填充的格式化"""
    result = f"{v[0:4]}-{v[4:6]}-{v[6:8]} 0{v[8:9]}:{v[9:11]}:00"
    return result

if __name__ == "__main__":
    # 测试
    test_v1 = "20240101"
    test_v2 = "202401011230"
    test_v3 = "20240101123045"
    test_v4 = "2024010112300"
    
    print(f"format_time_v1: {format_time_v1(test_v1)}")
    print(f"format_time_v2: {format_time_v2(test_v3)}")
    print(f"format_time_v3(8): {format_time_v3(test_v1)}")
    print(f"format_time_v3(12): {format_time_v3(test_v2)}")
    print(f"format_time_v3(14): {format_time_v3(test_v3)}")

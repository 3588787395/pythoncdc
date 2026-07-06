#!/usr/bin/env python3
"""
测试切片比较问题 - 从quote.pyc提取的关键问题

这是CFG模式中最严重的问题之一：
切片比较操作被错误地反编译为空条件

原始代码:
```python
if start[:8] < listing_date[:8]:
    start = listing_date
```

错误反编译:
```python
if :8:
    start = listing_date
```
"""

def simple_slice_comparison(start, listing_date):
    """简单的切片比较"""
    if start[:8] < listing_date[:8]:
        return True
    return False

def slice_comparison_with_assignment(start, end, listing_date, delivery_date):
    """切片比较并赋值 - quote.pyc中的实际案例"""
    if listing_date:
        if delivery_date:
            if start[:8] < listing_date[:8]:
                start = listing_date
    
    if delivery_date:
        if end[:8] > delivery_date[:8]:
            end = delivery_date
    
    return (start, end)

def nested_slice_comparison(x, y, z):
    """嵌套切片比较"""
    if x[:4] == y[:4]:
        if x[4:6] < y[4:6]:
            return "month_less"
        elif x[4:6] > y[4:6]:
            return "month_greater"
        else:
            if x[6:8] < y[6:8]:
                return "day_less"
    return "other"

def slice_in_condition(data, threshold):
    """切片在复杂条件中"""
    if len(data) > 10:
        prefix = data[:8]
        if prefix < threshold[:8]:
            return "less"
        elif prefix > threshold[:8]:
            return "greater"
    return "unknown"

def multiple_slice_comparisons(date1, date2):
    """多个切片比较"""
    year1 = date1[:4]
    year2 = date2[:4]
    month1 = date1[4:6]
    month2 = date2[4:6]
    day1 = date1[6:8]
    day2 = date2[6:8]
    
    if year1 < year2:
        return -1
    elif year1 > year2:
        return 1
    else:
        if month1 < month2:
            return -1
        elif month1 > month2:
            return 1
        else:
            if day1 < day2:
                return -1
            elif day1 > day2:
                return 1
            else:
                return 0

if __name__ == "__main__":
    # 测试
    print(f"simple_slice_comparison: {simple_slice_comparison('20240101', '20240102')}")
    
    result = slice_comparison_with_assignment('20230101', '20251231', '20240101', '20241231')
    print(f"slice_comparison_with_assignment: {result}")
    
    print(f"nested_slice_comparison: {nested_slice_comparison('20240115', '20240201', '')}")
    
    print(f"slice_in_condition: {slice_in_condition('20240101120000', '20240102')}")
    
    print(f"multiple_slice_comparisons: {multiple_slice_comparisons('20240101', '20240102')}")

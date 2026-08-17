#!/usr/bin/env python3
"""最小复现实例生成脚本 - Round 61"""

import os
import dis
from pathlib import Path

# 创建复现实例目录
repro_dir = Path(".trae/specs/region-comment-multi-pyc-iteration/rounds/round_61/test_engineer/minimal_repros")
repro_dir.mkdir(parents=True, exist_ok=True)

# 复现实例模板（基于 Pattern P1: try-except 嵌套参数解包）
repro_templates = [
    # Pattern P1: 参数解包 + try-except
    ("""def func_with_args_and_try(a, b, c):
    try:
        result = process(a, b)
        return result
    except Exception as e:
        log(e)
        return None
""", "repro_01_param_unpack_try.py", "参数解包 + try-except"),

    # Pattern P1 变体: 多个参数 + 嵌套异常
    ("""def multi_param_nested_try(x, y, z, w):
    try:
        r1 = op1(x, y)
        r2 = op2(z, w)
        return (r1, r2)
    except ValueError:
        return (0, 0)
""", "repro_02_multi_param_nested.py", "多参数嵌套 try"),

    # Pattern P2: 字段赋值 + try-except
    ("""def fields_assignment_with_try(data):
    fields = ['a', 'b', 'c']
    try:
        result = process_fields(fields, data)
        return result
    except:
        return None
""", "repro_03_fields_assign_try.py", "字段赋值 + try-except"),

    # Pattern P2 变体: 属性访问 + 逻辑判断
    ("""def attr_access_with_cond(obj):
    fields = obj.fields if hasattr(obj, 'fields') else []
    for f in fields:
        try:
            val = getattr(obj, f)
            if val:
                print(val)
        except:
            pass
""", "repro_04_attr_access_cond.py", "属性访问 + 条件"),

    # Pattern P3: 复杂控制流 + try-except
    ("""def complex_control_flow_with_try(query_date, fields):
    result = []
    try:
        if query_date:
            for f in fields:
                data = fetch(f, query_date)
                result.append(data)
        else:
            result = get_default(fields)
        return result
    except Exception as e:
        log(e)
        return []
""", "repro_05_complex_control_try.py", "复杂控制流 + try"),

    # 控制组：简单参数解包（应能正确处理）
    ("""def simple_param_unpack(a, b):
    x, y = a, b
    return x + y
""", "repro_06_ctrl_simple_unpack.py", "控制组：简单参数解包"),

    # 控制组：简单 try-except
    ("""def simple_try_except(x):
    try:
        return process(x)
    except:
        return None
""", "repro_07_ctrl_simple_try.py", "控制组：简单 try-except"),

    # Pattern P1/P2 组合：解包 + try + 属性访问
    ("""def unpack_try_attr(obj, params):
    a, b = params
    try:
        result = method(a, b)
        return obj.attr if result else None
    except:
        return None
""", "repro_08_unpack_try_attr.py", "解包 + try + 属性访问"),

    # Pattern P3 变体：循环 + try-except
    ("""def loop_try_except(items, fields):
    results = []
    for item in items:
        try:
            for f in fields:
                val = item.get(f)
                results.append(val)
        except:
            continue
    return results
""", "repro_09_loop_try.py", "循环 + try-except"),

    # Pattern P2 变体：列表构建 + 异常处理
    ("""def list_build_with_exception(data):
    fields = data.keys() if data else []
    try:
        result = [process(f, data) for f in fields]
        return result
    except:
        return []
""", "repro_10_list_build_try.py", "列表构建 + 异常"),

    # Pattern P1 嵌套变体：try-except 中的参数解包
    ("""def nested_try_unpack(x):
    try:
        a, b = split(x)
        try:
            return compute(a, b)
        except:
            return (a, None)
    except:
        return (None, None)
""", "repro_11_nested_try_unpack.py", "嵌套 try + 参数解包"),

    # 控制组：正常函数（应 100% 一致）
    ("""def normal_function(a, b):
    return a + b
""", "repro_12_ctrl_normal.py", "控制组：正常函数"),
]

# 写入所有复现实例
for source, filename, description in repro_templates:
    filepath = repro_dir / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"""# {description}
# Minimal reproduction for Round 61 - Pattern Analysis
#
# Target Pattern: {description.split(':', 1)[1].strip() if ':' in description else description}
#
{source}
""")

print(f"已创建 {len(repro_templates)} 个最小复现实例到 {repro_dir}")

# 列表输出
print("\n复现实例列表：")
for i, (source, filename, description) in enumerate(repro_templates, 1):
    print(f"  {i:2d}. {filename:40s} - {description}")
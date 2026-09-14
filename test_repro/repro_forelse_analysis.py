"""
for-else / while-else 识别错误分类报告
=====================================

## 核心发现

### Bug #1: for-else 中 break 被替换为 continue（最关键bug）

触发条件：for-else 循环中，break 语句前面有至少一条非空语句（赋值、方法调用等）

原始字节码模式：
  ... 语句（如 found = True / result.append(item)）...
  POP_TOP                    # 弹出迭代器值（break清理）
  JUMP_FORWARD <offset>      # break - 跳过 else 块
  JUMP_BACKWARD <offset>     # continue - 循环回跳

反编译后字节码：
  ... 语句 ...
  JUMP_BACKWARD <offset>     # 错误！break被替换为continue

影响：
  - else 块永远执行（因为 break 变成 continue，循环总是正常结束）
  - 语义完全改变：原本只在循环正常结束时执行的 else 块，变成了无条件执行

最小复现：
  def for_else_break_bug(data, key):
      found = False
      for item in data:
          if item == key:
              found = True      # <-- 这条语句导致 break 被错误识别
              break
      else:
          found = False         # <-- 此 else 块在反编译后永远执行
      return found

### Bug #2: for-else 中 else 块完全丢失

触发条件：for-else 循环中包含 return 语句（而非 break），或
         for-else 位于 try-except 块内

原始字节码：
  FOR_ITER -> target
  ... loop body with return ...
  JUMP_BACKWARD
  JUMP_FORWARD -> else_start    # else 块开始标记
  ... else body ...

反编译后：else 块的 JUMP_FORWARD 被省略，else 体内的代码变成无条件执行

### Bug #3: for-else 中 JUMP_FORWARD 目标偏移错误

触发条件：for-else 循环后有复杂控制流（嵌套 if-elif、try-except 等）

原始字节码：JUMP_FORWARD target = N（正确的 else 块结束位置）
反编译后：JUMP_FORWARD target = M（M < N，else 块被截断）

### Bug #4: while-else 中 else 块与异常处理混淆

触发条件：while-else 位于 try-except 块内，else 块的 JUMP_FORWARD
         目标与 except 处理器重叠

### Bug #5: for-else 中多个 break 点部分丢失

触发条件：for-else 循环中有多个 break（不同条件分支）
         部分break被正确识别，部分被替换为continue

## 不触发的模式

- for-else with bare break（break前无语句）→ 正确
- while-else with break → 正确（因为while没有迭代器POP_TOP）
- 简单的 for-else without break → 正确

## 根因分析

Python 3.11 中，for 循环的 break 生成 POP_TOP + JUMP_FORWARD：
  - POP_TOP: 清理迭代器栈上的值（for循环 break 必需）
  - JUMP_FORWARD: 跳过 else 块到循环后代码

反编译器错误地将 POP_TOP 归属于前一条语句（如 STORE_FAST 的结果），
导致无法识别 POP_TOP + JUMP_FORWARD 是 break 模式，误将其生成
为 JUMP_BACKWARD（continue）。

while 循环的 break 不需要 POP_TOP（没有迭代器），所以 while-else
不受此bug影响。
"""

# === 验证用最小复现实例 ===

# Instance 1: 赋值 + break（核心bug）
def repro1_assign_before_break(data, key):
    found = False
    for item in data:
        if item == key:
            found = True
            break
    else:
        found = False
    return found

# Instance 2: 方法调用 + break
def repro2_method_before_break(data, key):
    result = []
    for item in data:
        if item == key:
            result.append(item)
            break
    else:
        result.append('not_found')
    return result

# Instance 3: 多个赋值 + break
def repro3_multi_assign_before_break(data, key):
    found = False
    value = None
    for item in data:
        if item == key:
            found = True
            value = item
            break
    else:
        found = False
    return found

# Instance 4: 嵌套if中的 break
def repro4_nested_if_break(data, key1, key2):
    found = False
    for item in data:
        if item == key1:
            if key2 is not None:
                found = True
                break
    else:
        found = False
    return found

# Instance 5: 多个break点
def repro5_multiple_breaks(data, key1, key2):
    result = []
    for item in data:
        if item == key1:
            result.append('found1')
            break
        if item == key2:
            result.append('found2')
            break
    else:
        result.append('not_found')
    return result

# Instance 6: return 代替 break（else块丢失）
def repro6_return_not_break(data, key):
    fp = None
    for item in data:
        if item == key:
            return item
    else:
        fp = 'closed'
    return fp

# Instance 7: for-else inside try-except
def repro7_try_except(data, key):
    result = []
    try:
        for item in data:
            if item == key:
                result.append(item)
                break
        else:
            result.append('processed_all')
    except Exception:
        result.append('error')
    return result

# Instance 8: for-else with continue in body
def repro8_continue_in_body(data, filter_fn):
    result = []
    for item in data:
        if filter_fn(item):
            result.append(item)
            continue
        result.append('skipped')
    else:
        result.append('completed')
    return result

# Instance 9: nested for-else
def repro9_nested_for_else(data, inner_check):
    outer_result = []
    for group in data:
        inner_result = []
        for item in group:
            if inner_check(item):
                result = [item]
                break
        else:
            inner_result.append('default')
        outer_result.extend(inner_result)
    else:
        outer_result.append('all_processed')
    return outer_result

# Instance 10: for-else with with-statement in else
def repro10_with_in_else(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item)
            continue
        result.append('skipped')
        continue
    else:
        result.append('done')
    return result

# Instance 11: for-else where else is just assignment
def repro11_else_just_assignment(data):
    result_dict = {}
    for item in data:
        key = item.get('id')
        if key:
            result_dict[key] = item
    else:
        data = list(result_dict.values())
    return data

# Instance 12: for-else with SWAP/POP_TOP return optimization
def repro12_swap_return(data, key):
    fp = None
    for item in data:
        if item == key:
            return item
    else:
        if fp is not None:
            fp = 'closed'
    return None

print("All 12 reproduction instances defined.")
print("Confirmed bugs: repro1, repro2, repro3, repro4, repro5 (break->continue)")
print("Suspected bugs: repro6, repro7 (else block lost/merged)")

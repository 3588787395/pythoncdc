"""生成 R8 的 10 个最小复现实例（每个 py_compile 验证），镜像 quotation.pyc 8 个不一致函数的缺陷模式。"""
import os, py_compile

OUT = '/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_08/test_engineer/minimal_repros'
os.makedirs(OUT, exist_ok=True)

REPROS = {}

# repro_01: one_prod_to_dataframe —— elif 链条件被外层 if(i==0) 污染 + len(v)==N 比较丢失
# 区域: Conditional/BoolOp  违反: 原则2(每块唯一归属) + 原则4(入口引用语义)
REPROS['repro_01_elif_chain_cond_polluted.py'] = '''"""R8 repro_01: one_prod_to_dataframe elif 链条件污染。
缺陷: 外层 `if i == 0:` 的条件被错误附加到内层 elif 条件上 (`elif i == 0 and len(v)==10`)，
且部分 elif 的 `len(v)==N` 比较被丢弃变为裸 `elif i == 0:`，导致 +10 指令差异。
区域类型: Conditional + BoolOp  违反原则: 2(每块唯一归属) + 4(入口引用语义)
"""
def f(fields, prod):
    index = []
    i = 0
    for v in prod:
        if i == 0:
            if len(v) == 8:
                index.append(v)
            elif len(v) == 10:
                index.append(v)
            elif len(v) == 9:
                index.append(v)
            elif len(v) == 12:
                index.append(v)
            elif len(v) == 14:
                index.append(v)
        i = i + 1
    return index
'''

# repro_02: load_bars_from_hundsun —— source_start 赋值被错误提升到 if os.path.exists 内 if typet==6 之前
# 区域: Conditional  违反: 原则1(自底向上归约)
REPROS['repro_02_assign_hoisted_before_nested_if.py'] = '''"""R8 repro_02: load_bars_from_hundsun 赋值语句错误提升。
缺陷: `source_start = strptime(...)` 被错误提升到 `if os.path.exists(...)` 块内 `if typet==6:` 之前，
原始位置在该赋值应出现在更内层/更后位置，导致 -88 指令差异(整体结构错位)。
区域类型: Conditional  违反原则: 1(自底向上归约)
"""
import os
def f(stocks, typet, start, end, path):
    data = {}
    retpanel = {}
    if os.path.exists(path):
        if typet == 6:
            if isinstance(stocks, str):
                stocks = [stocks]
            daily = {}
            if not daily:
                source_end = start + end
                diffset = set(stocks)
                if len(diffset) == 0:
                    retpanel = daily
                    return retpanel
                elif len(diffset) < len(stocks):
                    retpanel = daily
                    stocks = list(diffset)
    if len(start) > 8:
        start_temp = start[:8]
    else:
        start_temp = start
    return retpanel
'''

# repro_03: get_str_data —— 嵌套 for 循环 + 循环后构造丢失
# 区域: Loop  违反: 原则2(每块唯一归属)
REPROS['repro_03_nested_for_post_construct_drop.py'] = '''"""R8 repro_03: get_str_data 嵌套 for 循环后构造丢失。
缺陷: 外层 for 循环体内的语句及循环后构造语句被部分丢弃，导致 -48 指令差异。
区域类型: Loop  违反原则: 2(每块唯一归属)
"""
def f(rdata, count, typet):
    order_data = {}
    for stock in rdata:
        stock_df = rdata[stock]
        dates = []
        for i in stock_df:
            dates.append(i)
        n = len(stock_df)
        datass_list = []
        datas_index = []
        j = 0
        while j < n:
            if dates[i] == dates[j]:
                datas_index.append(j)
                i = j
                j += 1
            else:
                datass_list.append(datas_index)
                datas_index = []
                i = j
                j += 1
        order_data[stock] = datass_list
    return order_data
'''

# repro_04: change_his_to_backward —— for 循环 + 循环后语句丢失
# 区域: Loop  违反: 原则2(每块唯一归属)
REPROS['repro_04_for_loop_post_stmt_drop.py'] = '''"""R8 repro_04: change_his_to_backward for 循环后语句丢失。
缺陷: for 循环体内及循环后语句被部分丢弃，导致 -57 指令差异。
区域类型: Loop  违反原则: 2(每块唯一归属)
"""
def f(security, data, exrights, start, end, typet):
    dates = list(data.index)
    for i in range(len(dates)):
        d = dates[i]
        if d in exrights:
            ex = exrights[d]
            if typet == 6:
                data.loc[d, 'open'] = data.loc[d, 'open'] * ex
                data.loc[d, 'close'] = data.loc[d, 'close'] * ex
            else:
                data.loc[d, 'open'] = data.loc[d, 'open'] / ex
        i = i + 1
    result = data.fillna(0)
    return result
'''

# repro_05: get_date_and_count —— if/elif 链语句丢失
# 区域: Conditional  违反: 原则4(入口引用语义)
REPROS['repro_05_if_elif_chain_stmt_drop.py'] = '''"""R8 repro_05: get_date_and_count if/elif 链语句丢失。
缺陷: if/elif/else 链中部分分支语句被丢弃，导致 -27 指令差异。
区域类型: Conditional  违反原则: 4(入口引用语义)
"""
def f(query_date, count, candle_period):
    end_time_str = str(query_date)[:8]
    weekday = 0
    if weekday in (6, 7):
        start_date = end_time_str - count * 7 - weekday
    else:
        start_date = end_time_str - count * 7
    trade_days = []
    d = start_date
    while d <= end_time_str:
        if weekday not in (6, 7):
            trade_days.append(d)
        elif candle_period == 1:
            trade_days.append(d)
        elif candle_period == 2:
            trade_days.append(d)
        d = d + 1
    return trade_days
'''

# repro_06: load_get_price —— 嵌套 if 含 BoolOp 链
# 区域: Conditional + BoolOp  违反: 原则3(嵌套即抽象节点)
REPROS['repro_06_nested_if_with_boolop_chain.py'] = '''"""R8 repro_06: load_get_price 嵌套 if 含 BoolOp 链语句丢失。
缺陷: `if is_utc == '0':` 分支下的 `elif typet == 1 or typet == 2 or ...` BoolOp 链所在分支语句丢失，导致 -26 指令差异。
区域类型: Conditional + BoolOp  违反原则: 3(嵌套即抽象节点)
"""
def f(panel, typet, is_utc):
    if len(panel) != 0:
        if is_utc == '0':
            panel = panel.convert('Asia/Shanghai')
        elif typet == 1 or typet == 2 or typet == 3 or typet == 4 or typet == 5 or typet == 13:
            panel = panel.localize('UTC').convert('Asia/Shanghai')
    panel = panel.localize(None)
    return panel
'''

# repro_07: build_future_fill_time —— listcomp 内部 code 对象差异 + 跳转目标偏移
# 区域: Loop + listcomp  违反: 原则3(嵌套即抽象节点)
REPROS['repro_07_listcomp_codeobj_diff.py'] = '''"""R8 repro_07: build_future_fill_time listcomp code 对象差异。
缺陷: 函数内 3 个 listcomp 中某个的内部 code 对象与原始不一致，引发后续跳转目标偏移(instr_diff)。
区域类型: Loop + listcomp  违反原则: 3(嵌套即抽象节点)
"""
def f(start, end, holidays):
    all_days = range(start, end)
    trade_days = [d for d in all_days if d not in holidays]
    am = [d for d in trade_days if d < 12]
    pm = [d for d in trade_days if d >= 13]
    result = []
    for d in trade_days:
        if d in am:
            result.append(('am', d))
        elif d in pm:
            result.append(('pm', d))
    return result
'''

# repro_08: BoolOp 链在 elif 上下文
# 区域: BoolOp  违反: 原则4(入口引用语义)
REPROS['repro_08_boolop_chain_in_elif.py'] = '''"""R8 repro_08: BoolOp 链在 elif 上下文条件丢失。
缺陷: `elif a == 1 or a == 2 or a == 3:` 形式的 BoolOp 链在 elif 上下文中部分条件丢失。
区域类型: BoolOp  违反原则: 4(入口引用语义)
"""
def f(a, b):
    if a == 0:
        return b
    elif a == 1 or a == 2 or a == 3 or a == 4 or a == 5 or a == 13:
        b = b + 1
        return b
    elif a == 6:
        b = b + 2
        return b
    return b
'''

# repro_09: for 循环体尾部 STORE_SUBSCR 赋值丢失
# 区域: Loop  违反: 原则2(每块唯一归属)
REPROS['repro_09_for_tail_subscr_assign_drop.py'] = '''"""R8 repro_09: for 循环体尾部 STORE_SUBSCR 赋值丢失。
缺陷: for 循环体尾部的 `obj[key] = value` 形式赋值被丢弃，循环后构造语句也部分丢失。
区域类型: Loop  违反原则: 2(每块唯一归属)
"""
def f(items):
    result = {}
    for k in items:
        v = items[k]
        if v is not None:
            result[k] = v
        result['count'] = len(result)
    total = sum(result.values())
    return total
'''

# repro_10: 三元表达式在条件上下文 + 后续 STORE 赋值
# 区域: Ternary + Conditional  违反: 原则2(每块唯一归属)
REPROS['repro_10_ternary_in_cond_with_post_store.py'] = '''"""R8 repro_10: 三元表达式在条件上下文 + 后续 STORE 赋值丢失。
缺陷: `x = a if cond else b` 三元表达式后的独立 `y = ...` 赋值被错误并入三元归约范围而丢失。
区域类型: Ternary + Conditional  违反原则: 2(每块唯一归属)
"""
def f(start, end):
    if len(start) > 8:
        source_start = start[:8] + (start[8:] if len(start[8:]) == 4 else '0000')
        source_end = end[:8] + (end[8:] if len(end[8:]) == 4 else '1530')
        diff = set(start).difference(set(end))
        if len(diff) == 0:
            return source_start
    return source_end if 'source_end' in dir() else None
'''

results = []
for name, content in REPROS.items():
    path = os.path.join(OUT, name)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(content)
    try:
        py_compile.compile(path, doraise=True)
        results.append((name, 'OK'))
    except py_compile.PyCompileError as e:
        results.append((name, f'FAIL: {e}'))

print("=== R8 minimal_repros generation ===")
for name, status in results:
    print(f"  {name}: {status}")
print(f"total: {len(results)}  all_ok={all(s=='OK' for _,s in results)}")

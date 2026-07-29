"""生成 R9 的 10 个最小复现实例（每个 py_compile 验证），镜像 quotation.pyc 5 个 len_diff 不一致函数 + Loop/Conditional 嵌套缺陷模式。"""
import os, py_compile

OUT = '/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_09/test_engineer/minimal_repros'
os.makedirs(OUT, exist_ok=True)

REPROS = {}

# repro_01: change_his_to_backward —— for 循环体内嵌套 if 的 else 分支体丢失（else_stmts_check 探针副作用）
# 区域: Loop + Conditional  违反: 原则2(每块唯一归属) + 原则4(入口引用语义)
REPROS['repro_01_loop_nested_if_else_body_drop.py'] = '''"""R9 repro_01: change_his_to_backward for 循环内嵌套 if 的 else 分支体丢失。
缺陷: for 循环体内 `if len(...)==0:` 的 else 分支体整段丢失(变 pass)，
根因 _if_generate_then_branch 用 _if_generate_else_branch 作探针有副作用(预标记 generated_blocks)，
正规调用时 else 块已标记为已生成而返回空。
区域类型: Loop + Conditional  违反原则: 2(每块唯一归属) + 4(入口引用语义)
"""
def f(indexlist, data, series, fields):
    preindex = None
    tmpdata = None
    predataindex = None
    for n in indexlist:
        if preindex is None:
            tmpdata = data[:n].copy()
            preindex = n
            predataindex = n
        elif data[predataindex:n].empty:
            break
        elif n in data.index:
            y = n + 'end'
            if len(data[predataindex:y]) == 0:
                pass
            else:
                data.loc[predataindex:y, fields] = round(data[predataindex:y][fields] * 1.0 + 2.0, 2)
                tmpdata = tmpdata.append(data[predataindex:y])
        else:
            data.loc[predataindex:n, fields] = round(data[predataindex:n][fields] * 1.0 + 2.0, 2)
            tmpdata = tmpdata.append(data[predataindex:n])
    if predataindex and len(data[predataindex:]) > 0:
        tmpdata = tmpdata.append(data[predataindex:])
    return tmpdata
'''

# repro_02: change_his_to_backward 简化 —— 空 then + else 体（探针副作用核心模式）
# 区域: Conditional  违反: 原则2(每块唯一归属)
REPROS['repro_02_empty_then_with_else_body.py'] = '''"""R9 repro_02: 空 then + else 体模式（else_stmts_check 探针副作用核心）。
缺陷: `if cond: pass else: <body>` 的 else body 丢失，因 then 为空时探针调用预标记 else 块。
区域类型: Conditional  违反原则: 2(每块唯一归属)
"""
def f(items):
    result = []
    for x in items:
        if x == 0:
            pass
        else:
            result.append(x * 2)
            result.append(x + 1)
    return result
'''

# repro_03: load_bars_from_hundsun —— if os.path.exists 内嵌套赋值 + if 链语句丢失
# 区域: Conditional  违反: 原则1(自底向上归约)
REPROS['repro_03_nested_if_assign_chain_drop.py'] = '''"""R9 repro_03: load_bars_from_hundsun 嵌套 if 内赋值与 if 链语句丢失(-88)。
缺陷: if os.path.exists 内 source_start 赋值 + if typet==6 内 dailypanel 赋值 + diffset if/elif 链语句部分丢失。
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
                source_start = start[:8]
                source_end = end[:8]
                diffset = set(stocks).difference(set(daily))
                if len(diffset) == 0:
                    retpanel = daily
                    return retpanel
                elif len(diffset) < len(stocks):
                    section = list(set(stocks).intersection(set(daily)))
                    retpanel = {k: daily[k] for k in section}
                    stocks = list(diffset)
    if len(start) > 8:
        start_temp = start[:8]
    else:
        start_temp = start
    return retpanel
'''

# repro_04: get_str_data —— 嵌套 for + while 循环体语句丢失
# 区域: Loop  违反: 原则2(每块唯一归属)
REPROS['repro_04_nested_for_while_body_drop.py'] = '''"""R9 repro_04: get_str_data 嵌套 for+while 循环体语句丢失(-48)。
缺陷: 外层 for 循环体内赋值 + 内层 while 循环体 if/else 分支语句部分丢失。
区域类型: Loop  违反原则: 2(每块唯一归属)
"""
def f(rdata):
    order_data = {}
    for stock in rdata:
        stock_df = rdata[stock]
        dates = list(stock_df.index)
        n = len(stock_df)
        datass_list = []
        datas_index = []
        i = 0
        j = 0
        while j < n:
            if dates[i] == dates[j]:
                datas_index.append(j)
                i = j
                j = j + 1
            else:
                datass_list.append(datas_index)
                datas_index = []
                i = j
                j = j + 1
        order_data[stock] = datass_list
    return order_data
'''

# repro_05: get_date_and_count —— while 循环 + if/elif 链语句丢失
# 区域: Loop + Conditional  违反: 原则4(入口引用语义)
REPROS['repro_05_while_if_elif_chain_drop.py'] = '''"""R9 repro_05: get_date_and_count while 循环 if/elif 链语句丢失(-27)。
缺陷: while 循环体内 if/elif/else 链部分分支语句丢失。
区域类型: Loop + Conditional  违反原则: 4(入口引用语义)
"""
def f(start, end, candle_period):
    trade_days = []
    d = start
    weekday = 0
    while d <= end:
        if weekday not in (6, 7):
            trade_days.append(d)
        elif candle_period == 1:
            trade_days.append(d)
            d = d + 1
        elif candle_period == 2:
            trade_days.append(d)
            d = d + 1
        else:
            d = d + 1
    return trade_days
'''

# repro_06: load_get_price —— 嵌套 if 含 BoolOp 链分支语句丢失
# 区域: Conditional + BoolOp  违反: 原则3(嵌套即抽象节点)
REPROS['repro_06_nested_if_boolop_branch_drop.py'] = '''"""R9 repro_06: load_get_price 嵌套 if 含 BoolOp 链分支语句丢失(-26)。
缺陷: `if is_utc == '0':` 与 `elif typet==1 or typet==2 or ...` BoolOp 链分支语句部分丢失。
区域类型: Conditional + BoolOp  违反原则: 3(嵌套即抽象节点)
"""
def f(panel, typet, is_utc):
    if len(panel) != 0:
        if is_utc == '0':
            panel = panel.convert('Asia/Shanghai')
            panel = panel.fillna(0)
        elif typet == 1 or typet == 2 or typet == 3 or typet == 4 or typet == 5 or typet == 13:
            panel = panel.localize('UTC').convert('Asia/Shanghai')
            panel = panel.fillna(0)
    panel = panel.localize(None)
    return panel
'''

# repro_07: for 循环后语句 + 循环内 break/continue 丢失
# 区域: Loop  违反: 原则2(每块唯一归属)
REPROS['repro_07_loop_break_continue_post_drop.py'] = '''"""R9 repro_07: for 循环内 break/continue + 循环后语句丢失。
缺陷: for 循环体内 break 与循环后构造语句被部分丢弃。
区域类型: Loop  违反原则: 2(每块唯一归属)
"""
def f(items, target):
    found = None
    for x in items:
        if x == target:
            found = x
            break
        elif x > target:
            continue
        else:
            found = x
    if found is not None:
        result = [found]
        result.append(found + 1)
        return result
    return []
'''

# repro_08: for 循环内嵌套 if/elif/else 多层缩进
# 区域: Loop + Conditional  违反: 原则3(嵌套即抽象节点)
REPROS['repro_08_loop_deep_nested_if_elif.py'] = '''"""R9 repro_08: for 循环内多层嵌套 if/elif/else 语句丢失。
缺陷: for 循环体内 3 层嵌套 if/elif/else 的深层分支语句丢失。
区域类型: Loop + Conditional  违反原则: 3(嵌套即抽象节点)
"""
def f(records):
    out = []
    for rec in records:
        if rec['type'] == 'a':
            if rec['sub'] == 1:
                out.append(rec['val'] * 2)
            elif rec['sub'] == 2:
                if rec['flag']:
                    out.append(rec['val'] + 10)
                else:
                    out.append(rec['val'] + 20)
            else:
                out.append(rec['val'])
        elif rec['type'] == 'b':
            out.append(rec['val'] - 1)
        else:
            out.append(0)
    return out
'''

# repro_09: while 循环 + 循环条件赋值丢失
# 区域: Loop  违反: 原则2(每块唯一归属)
REPROS['repro_09_while_cond_assign_drop.py'] = '''"""R9 repro_09: while 循环条件赋值与循环体语句丢失。
缺陷: while 循环前/内的条件赋值及循环体末尾语句丢失。
区域类型: Loop  违反原则: 2(每块唯一归属)
"""
def f(data, limit):
    i = 0
    total = 0
    while i < len(data):
        cur = data[i]
        if cur > limit:
            total = total + cur
            i = i + 1
        else:
            i = i + 1
            continue
    avg = total / len(data) if len(data) > 0 else 0
    return avg
'''

# repro_10: for 循环 + STORE_SUBSCR 赋值 + 循环后聚合
# 区域: Loop  违反: 原则2(每块唯一归属)
REPROS['repro_10_loop_subscr_assign_aggregate.py'] = '''"""R9 repro_10: for 循环 STORE_SUBSCR 赋值 + 循环后聚合语句丢失。
缺陷: for 循环体内 obj[key]=value 赋值与循环后聚合语句丢失。
区域类型: Loop  违反原则: 2(每块唯一归属)
"""
def f(rows):
    result = {}
    for row in rows:
        k = row['key']
        v = row['val']
        if k in result:
            result[k] = result[k] + v
        else:
            result[k] = v
        result['count'] = len(result)
    total = sum(result.values())
    return total
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

print("=== R9 minimal_repros generation ===")
for name, status in results:
    print(f"  {name}: {status}")
print(f"total: {len(results)}  all_ok={all(s=='OK' for _,s in results)}")

"""生成 R10 的 10 个最小复现实例（每个 py_compile 验证），镜像 quotation.pyc 残留 7 个不一致函数的缺陷模式。"""
import os, py_compile

OUT = '/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_10/test_engineer/minimal_repros'
os.makedirs(OUT, exist_ok=True)

REPROS = {}

# repro_01: load_bars_from_hundsun（R10 已修复）—— BoolOp 子表达式赋值被提升到外层 IfRegion
# 区域: Conditional + BoolOp  违反: 原则1(自底向上归约) + 原则2(每块唯一归属)
REPROS['repro_01_boolop_assign_hoisted_out_of_nested_if.py'] = '''"""R10 repro_01: load_bars_from_hundsun BoolOp 子表达式赋值被提升到外层 IfRegion（R10 已修复）。
缺陷: `source_start = strptime(start[:8] + (len(start[8:])==4 and start[8:] or '0000'), ...)` 含 BoolOp/ternary 子表达式，
该赋值块被错误归属到外层 IfRegion(os.path.exists) 而非内层 IfRegion(typet==6)，导致赋值被提升到 if typet==6 之前。
区域类型: Conditional + BoolOp  违反原则: 1(自底向上归约) + 2(每块唯一归属)
"""
import os
def f(stocks, typet, start, end, path):
    data = {}
    retpanel = {}
    if os.path.exists(path):
        if typet == 6:
            source_start = start[:8] + (start[8:] if len(start[8:]) == 4 else '0000')
            if isinstance(stocks, str):
                stocks = [stocks]
            daily = {}
            if not daily:
                source_end = end[:8] + (end[8:] if len(end[8:]) == 4 else '1530')
                diffset = set(stocks).difference(set(daily))
                if len(diffset) == 0:
                    retpanel = daily
                    return retpanel
                elif len(diffset) < len(stocks):
                    retpanel = {k: daily[k] for k in stocks if k in daily}
                    stocks = list(diffset)
    return retpanel
'''

# repro_02: get_str_data —— 嵌套 for + while 循环体语句丢失（残留 -48）
# 区域: Loop  违反: 原则2(每块唯一归属)
REPROS['repro_02_nested_for_while_body_drop.py'] = '''"""R10 repro_02: get_str_data 嵌套 for+while 循环体语句丢失（残留 -48）。
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

# repro_03: get_date_and_count —— while 循环 + if/elif 链语句丢失（残留 -27）
# 区域: Loop + Conditional  违反: 原则4(入口引用语义)
REPROS['repro_03_while_if_elif_chain_drop.py'] = '''"""R10 repro_03: get_date_and_count while 循环 if/elif 链语句丢失（残留 -27）。
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

# repro_04: load_get_price —— 嵌套 if 含 BoolOp 链分支语句丢失（残留 -2，R10 部分修复）
# 区域: Conditional + BoolOp  违反: 原则3(嵌套即抽象节点)
REPROS['repro_04_nested_if_boolop_branch_drop.py'] = '''"""R10 repro_04: load_get_price 嵌套 if 含 BoolOp 链分支语句丢失（残留 -2，R10 部分修复）。
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

# repro_05: build_future_fill_time —— listcomp code 对象 + 跳转目标偏移（instr_diff）
# 区域: Loop + listcomp  违反: 原则3(嵌套即抽象节点)
REPROS['repro_05_listcomp_codeobj_jump_target.py'] = '''"""R10 repro_05: build_future_fill_time listcomp code 对象 + 跳转目标偏移。
缺陷: 函数内 listcomp 的内部 code 对象与原始不一致，引发后续跳转目标偏移(instr_diff@226)。
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

# repro_06: one_prod_to_dataframe —— 跳转目标归一化差异（instr_diff@131，R8 已修复 len）
# 区域: Conditional  违反: 原则4(入口引用语义)
REPROS['repro_06_jump_target_normalization.py'] = '''"""R10 repro_06: one_prod_to_dataframe 跳转目标归一化差异（instr_diff@131，R8 已修复 len）。
缺陷: 反编译器将首个 `i==0` 提取为外层 if，原始跳到下一 elif，导致跳转目标偏移(语义等价)。
区域类型: Conditional  违反原则: 4(入口引用语义)
"""
def f(prod):
    index = []
    i = 0
    for v in prod:
        if i == 0 and len(v) == 8:
            index.append(v)
        elif i == 0 and len(v) == 10:
            index.append(v)
        elif i == 0 and len(v) == 9:
            index.append(v)
        i = i + 1
    return index
'''

# repro_07: <module> —— code 对象 filename 元数据差异（instr_diff@394）
# 区域: Sequence/Module  违反: 无（元数据差异，非算法缺陷）
REPROS['repro_07_module_codeobj_filename.py'] = '''"""R10 repro_07: <module> code 对象 filename 元数据差异（instr_diff@394）。
缺陷: 嵌套 code 对象的 co_filename 在原始为 './fly_docker_py311/fly/data/quotation.py'，
反编译产物为 '<decompiled>'，导致 LOAD_CONST code 对象比较不等(非语句丢失，元数据差异)。
区域类型: Sequence/Module  违反原则: 无（元数据差异，非算法缺陷）
"""
CONST = 1
def helper(x):
    return x + CONST
def main():
    return helper(2)
'''

# repro_08: change_his_to_backward —— 跳转目标归一化差异（instr_diff@296，R9 已修复 len）
# 区域: Loop + Conditional  违反: 原则4(入口引用语义)
REPROS['repro_08_jump_target_after_len_fix.py'] = '''"""R10 repro_08: change_his_to_backward 跳转目标归一化差异（instr_diff@296，R9 已修复 len）。
缺陷: for 循环内嵌套 if 的 else 体已恢复(R9)，残留跳转目标偏移(语义等价)。
区域类型: Loop + Conditional  违反原则: 4(入口引用语义)
"""
def f(indexlist, data):
    predataindex = None
    tmpdata = None
    for n in indexlist:
        if predataindex is None:
            tmpdata = data[:n].copy()
            predataindex = n
        elif n in data.index:
            y = n + 'end'
            if len(data[predataindex:y]) == 0:
                pass
            else:
                tmpdata = tmpdata.append(data[predataindex:y])
        else:
            tmpdata = tmpdata.append(data[predataindex:n])
    return tmpdata
'''

# repro_09: BoolOp post-STORE 语句重建（R10 修复点 3 模式）
# 区域: BoolOp  违反: 原则2(每块唯一归属)
REPROS['repro_09_boolop_post_store_reconstruct.py'] = '''"""R10 repro_09: BoolOp post-STORE 语句重建（R10 修复点 3 模式）。
缺陷: BoolOpRegion merge_block 在 value_target STORE 之后的独立赋值语句因 generated 检查返回空而丢失。
区域类型: BoolOp  违反原则: 2(每块唯一归属)
"""
def f(start, end, daily):
    if not daily:
        source_start = start[:8] + (start[8:] if len(start[8:]) == 4 else '0000')
        source_end = end[:8] + (end[8:] if len(end[8:]) == 4 else '1530')
        panel = daily.ix[:, source_start:source_end]
        diffset = set(start).difference(set(daily))
        if len(diffset) == 0:
            return panel
    return daily
'''

# repro_10: 双角色块检测（R10 修复点 2 模式）
# 区域: BoolOp  违反: 原则1(自底向上归约) + 原则4(入口引用语义)
REPROS['repro_10_dual_role_block_detection.py'] = '''"""R10 repro_10: 双角色块检测（R10 修复点 2 模式）。
缺陷: 前驱 BoolOp 的 merge_block 同时是当前 BoolOp 的 entry 时，未允许继续处理导致 source_end 赋值丢失。
区域类型: BoolOp  违反原则: 1(自底向上归约) + 4(入口引用语义)
"""
def f(a, b):
    x = a[:8] + (a[8:] if len(a[8:]) == 4 else '0000')
    y = b[:8] + (b[8:] if len(b[8:]) == 4 else '1530')
    result = {}
    if x and y:
        result['x'] = x
        result['y'] = y
    return result
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

print("=== R10 minimal_repros generation ===")
for name, status in results:
    print(f"  {name}: {status}")
print(f"total: {len(results)}  all_ok={all(s=='OK' for _,s in results)}")

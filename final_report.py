#!/usr/bin/env python3
"""
trade_live_broker.pyc - 19 个不一致函数的模式分析报告
=========================================================

1. 模式统计表
2. 每种模式的典型函数名和具体字节码差异
3. 最小复现实例
"""

# ═══════════════════════════════════════════════════════════════════════════════
# 1. 模式统计表
# ═══════════════════════════════════════════════════════════════════════════════
#
# 模式                | 出现次数 | 优先级 | 说明
# ────────────────────┼─────────┼───────┼─────────────────────────────────────────────
# P_FOR_ELSE          |    9    | HIGH   | while-else/for-else 子句识别错误
# P_TRY_EXCEPT        |    3    | MEDIUM | try-except-finally 边界/作用域错误
# P_TRUNCATE          |    3    | MEDIUM | 函数体截断（含 f-string ternary 缺陷）
# P_COND_INVERT       |    2    | MEDIUM | 条件跳转反转 + 块级联
# P_OTHER             |    2    | LOW    | 其他（LOAD_CONST 字符串差异 + 块级联）
#
# 注: P_TRUNCATE 中的 3 个函数（fund_transfer, market_fund_transfer,
#     on_strategy_signal_response）的根因实际是 f-string ternary 表达式
#     反编译后丢失尾部文字，导致整个代码块语义偏移。因此 P_TRUNCATE 的
#     根因模式可归为 P_FSTRING_TERNARY。
#
# 修正后的模式分类:
#
# 模式                    | 出现次数 | 优先级 | 根因
# ────────────────────────┼─────────┼───────┼──────────────────────────────
# P_FOR_ELSE              |    9    | HIGH   | while-else/for-else else子句丢失/错位
# P_FSTRING_TERNARY       |    3    | HIGH   | f-string ternary 表达式丢尾/误解析为集合
# P_TRY_EXCEPT            |    3    | MEDIUM | try-except 在 while 内部的块重排
# P_COND_INVERT           |    2    | MEDIUM | 条件跳转反转导致 if/else 体交换
# P_OTHER                 |    2    | LOW    | 常量字符串差异+代码块级联偏移

# ═══════════════════════════════════════════════════════════════════════════════
# 2. 每种模式的典型函数名和具体字节码差异
# ═══════════════════════════════════════════════════════════════════════════════

PATTERN_DETAILS = """
P_FOR_ELSE (9 functions) - while-else/for-else 子句识别错误
─────────────────────────────────────────────────────────────
典型函数: _process_cancel_order
  orig=295 dec=295 true_diffs=267

  first_diff (filtered index 13):
    orig:  LOAD_FAST('self')           ← while-else 的 else 子句代码开始
    decomp: JUMP_FORWARD(138)          ← 反编译器插入了跳转到 else 末尾的跳转

  字节码差异详情:
    orig (while-else 正确结构):
      12 POP_JUMP_FORWARD_IF_FALSE 2000   ← while 条件不满足时跳到 else 体
      13 LOAD_FAST 'self'                  ← else 体: self.lock.acquire()
      14 LOAD_ATTR 'lock'
      15 LOAD_METHOD 'acquire'
      ...
      31 JUMP_FORWARD 318                  ← else 体结束，跳过 try-except
      32 PUSH_EXC_INFO                     ← try 块开始

    decomp (错误重构):
      12 POP_JUMP_FORWARD_IF_FALSE 96      ← while 条件不满足时跳转
      13 JUMP_FORWARD 138                  ← 反编译器插入的跳转（跳到 while 后面）
      14 LOAD_GLOBAL 'time'                ← 错误：把 else 体当成了 while 外的代码
      15 LOAD_ATTR 'sleep'                 ← time.sleep(0.001)
      16 LOAD_CONST 0.001
      17 CALL 1
      18 POP_TOP
      19 JUMP_BACKWARD 44                 ← 回跳到 while 开头
      20 LOAD_FAST 'self'                  ← 错误位置

  根因: CPython 3.11 编译 while-else 时，else 子句的字节码紧跟 while 体之后，
  while 条件失败时 JUMP 到 else 体。反编译器将这个结构误解为：
    while True:
        if cond: body
        else: time.sleep(0.001); continue
  而实际源码是:
    while cond: body
    else: time.sleep(0.001)

所有 P_FOR_ELSE 函数:
  _process_cancel_order: orig=295 dec=295 td=267  first: LOAD_FAST(self) → JUMP_FORWARD(138)
  _process_order:        orig=454 dec=390 td=424  first: LOAD_FAST(self) → JUMP_FORWARD(138)
  _trade_status_handle:  orig=114 dec=116 td=74   first: LOAD_FAST(trade_status) → JUMP_FORWARD(338)
  _sync_worker:          orig=349 dec=314 td=290  first: POP_JUMP_IF_TRUE → POP_JUMP_IF_FALSE (条件反转+else错位)
  get_all_orders:        orig=79  dec=78  td=24   first: JUMP_FORWARD(362) → LOAD_DEREF(security) (else跳转丢失)
  get_etf_stock_info:    orig=144 dec=117 td=139  first: JUMP_FORWARD(56) → BUILD_LIST(0) (else块被替换)
  get_hks_list:          orig=232 dec=230 td=120  first: UNPACK_SEQUENCE(2) → STORE_FAST(redata) (else体错位)
  get_sort_msg:          orig=192 dec=190 td=34   first: UNPACK_SEQUENCE(2) → STORE_FAST(redata)
  ipo_stocks_order:      orig=1075 dec=1091 td=483 first: JUMP_FORWARD(3378) → LOAD_FAST(new_stock)
  submit_order:          orig=120 dec=121 td=37   first: JUMP_FORWARD(686) → LOAD_FAST(self)

─────────────────────────────────────────────────────────────
P_FSTRING_TERNARY (3 functions) - f-string ternary 表达式丢尾/误解析
─────────────────────────────────────────────────────────────
典型函数: fund_transfer
  orig=123 dec=87 true_diffs=57

  first_diff (filtered index 54):
    orig:  LOAD_GLOBAL('strategy_log')     ← strategy_log.error(...)
    decomp: LOAD_FAST('trans_direction')    ← 代码完全偏移，f-string 重建错误

  根因: f-string 中包含 ternary 表达式时，反编译器无法正确重建。
  具体表现:
    原始: return f"{'转入' if direction == '0' else '转出'}极{'沪A' if type == '1' else '深A'}"
    反编译: return f"strategy_log转入极沪A"  (或将 ternary 后的文字合并到变量名)
  
  反编译器把 f-string 的 BUILD_STRING + FORMAT_VALUE 序列错误重建，
  导致:
  1. ternary 表达式后的尾部文字丢失
  2. 函数名(strategy_log)被错误地拼接到字符串中
  3. 后续代码块整体偏移，级联影响整个函数

所有 P_FSTRING_TERNARY 函数:
  fund_transfer:            orig=123 dec=87  td=57  ratio=0.71 (截断严重)
  market_fund_transfer:     orig=94  dec=66  td=41  ratio=0.70 (截断严重)
  on_strategy_signal_response: orig=45 dec=29 td=26  ratio=0.64 (截断最严重)

─────────────────────────────────────────────────────────────
P_TRY_EXCEPT (3 functions) - try-except 在 while 内部的块重排
─────────────────────────────────────────────────────────────
典型函数: on_before_trading_start
  orig=287 dec=288 true_diffs=61

  first_diff (filtered index 227):
    orig:  JUMP_FORWARD(1662)            ← try 体结束，跳过 except handler
    decomp: JUMP_BACKWARD(1090)          ← 被误识为 while 回跳

  根因: CPython 3.11 在 while+try/except 结构中，try 体结束的 JUMP_FORWARD
  和 while 循环回跳的 JUMP_BACKWARD 相邻，反编译器混淆了两者边界。
  导致 except handler 被偏移 1 条指令，后续所有代码级联偏移。

所有 P_TRY_EXCEPT 函数:
  on_before_trading_start: orig=287 dec=288 td=61  first: JUMP_FORWARD → JUMP_BACKWARD
  etf_basket_order:        orig=693 dec=692 td=431 first: LOAD_GLOBAL(strategy_log) → LOAD_FAST(entrust_price)
  etf_purchase_redemption: orig=377 dec=354 td=102 first: LOAD_GLOBAL(strategy_log) → LOAD_CONST(strategy_log后端服务 )

─────────────────────────────────────────────────────────────
P_COND_INVERT (2 functions) - 条件跳转反转导致 if/else 体交换
─────────────────────────────────────────────────────────────
典型函数: _sync_worker
  orig=349 dec=314 true_diffs=290

  first_diff (filtered index 48):
    orig:  POP_JUMP_FORWARD_IF_TRUE(704)    ← while 条件: if x < pre_time skip else-body
    decomp: POP_JUMP_FORWARD_IF_FALSE(562)  ← 反转为: if not (x < pre_time) skip body

  根因: 反编译器将 while 条件的跳转方向反转，导致 if/else 体交换，
  后续所有指令偏移，产生数百条 true_diffs。
  compare_bytecode 的 _normalize_condition_inversion 只处理了同目标的反转，
  但这里跳转目标也变了（级联偏移），所以无法自动归一化。

所有 P_COND_INVERT 函数:
  _sync_worker:   orig=349 dec=314 td=290  first: POP_JUMP_IF_TRUE(704) → POP_JUMP_IF_FALSE(562)
  get_ipo_stocks: orig=453 dec=452 td=106  first: POP_JUMP_IF_FALSE(1918) → POP_JUMP_IF_TRUE(2082)

─────────────────────────────────────────────────────────────
P_OTHER (2 functions) - 常量字符串差异+代码块级联偏移
─────────────────────────────────────────────────────────────
典型函数: on_order_response
  orig=445 dec=446 true_diffs=182

  first_diff:
    orig:  LOAD_CONST('后端服务，当前主推%s为委托主推')
    decomp: LOAD_CONST('后端服务，委托主推%s未匹配到对应Order')

  根因: 反编译器将原始字符串错误重建，后续代码块因字符串长度差异
  导致整体偏移。可能涉及 f-string 重建或 %-format 字符串解析错误。

所有 P_OTHER 函数:
  on_order_response:  orig=445 dec=446 td=182
  on_trade_response:  orig=392 dec=393 td=140
"""

# ═══════════════════════════════════════════════════════════════════════════════
# 3. 最小复现实例 (已验证可复现)
# ═══════════════════════════════════════════════════════════════════════════════

MINIMAL_REPROS = """
═══════════════════════════════════════════════════════════════════
P_FOR_ELSE 最小复现实例 (5个，均已验证)
═══════════════════════════════════════════════════════════════════

Repro 1: while + if-break + elif + else-continue (td=8, jd=2)
─────────────────────────────────────────────────────────────
def handle(events):
    while len(events) > 0:
        event = events.pop(0)
        if event.type == 'stop':
            break
        elif event.type == 'signal':
            process(event)
        else:
            continue

反编译输出 (BUG):
def handle(events):
    while len(events) > 0:
        event = events.pop(0)
        if event.type == 'stop':
            return None          ← break 变成 return None
        if event.type == 'signal':  ← elif 变成 if
            process(event)       ← else: continue 被删除

Bug说明: 反编译器将 break 误为 return None，将 elif 变为 if，
删除 else: continue 分支。这是 while-else 边界识别错误的直接表现。

─────────────────────────────────────────────────────────────
Repro 2: while + pop + log + if-break + if-elif (td=27, jd=1)
─────────────────────────────────────────────────────────────
def handle(events):
    while len(events) > 0:
        event = events.pop(0)
        log.debug(str(event))
        if event == 'stop':
            break
        if event == 'signal':
            process(event)

反编译输出 (BUG):
def handle(events):
    while len(events) > 0:
        event = events.pop(0)
        if event == 'stop':
            return None
        if event == 'signal':
            process(event)

Bug说明: log.debug 调用被丢失，break 变为 return None。
循环内多个 if 分支的结构被重组。

─────────────────────────────────────────────────────────────
Repro 3: while + if-break + elif-continue (无 else)
─────────────────────────────────────────────────────────────
def handle(events):
    while len(events) > 0:
        event = events.pop(0)
        if event.type == 'stop':
            break
        elif event.type == 'skip':
            continue
        process(event)

(此变体未触发 bug - 说明 else: continue 是关键触发条件)

─────────────────────────────────────────────────────────────
Repro 4: for-else with break (对照)
─────────────────────────────────────────────────────────────
def search(items):
    for item in items:
        if item == 'target':
            break
    else:
        return None
    return item

(此变体未触发 bug - for-else-break 单独不足以触发)

─────────────────────────────────────────────────────────────
Repro 5: while + 多层 elif
─────────────────────────────────────────────────────────────
def handle(events):
    while len(events) > 0:
        event = events.pop(0)
        if event.type == 'stop':
            break
        elif event.type == 'signal':
            process(event)
        elif event.type == 'skip':
            continue
        else:
            log.debug('unknown')
            continue

(此变体未触发 bug - 更复杂的 elif 链不触发，说明 bug 对
 if-elif-else 的三段式结构敏感)


═══════════════════════════════════════════════════════════════════
P_FSTRING_TERNARY 最小复现实例 (5个，均已验证)
═══════════════════════════════════════════════════════════════════

Repro 1: f-string ternary + 中文尾部 (td=3, jd=0)
─────────────────────────────────────────────────────────────
def test(direction):
    return f"{'转入' if direction == '0' else '转出'}极"

反编译输出 (BUG):
def test(direction):
    return f"{'转入' if direction == '0' else '转出'}"

Bug说明: 尾部汉字 '极' 被丢失。
first_diff: LOAD_CONST('极') → RETURN_VALUE(None)

─────────────────────────────────────────────────────────────
Repro 2: f-string ternary + ASCII 尾部 (td=3, jd=0)
─────────────────────────────────────────────────────────────
def test(direction):
    return f"{'IN' if direction == '0' else 'OUT'}_FAIL"

反编译输出 (BUG):
def test(direction):
    return f"{'IN' if direction == '0' else 'OUT'}"

Bug说明: 尾部 '_FAIL' 被丢失。说明不是编码问题，而是通用的
f-string ternary 尾部丢失 bug。

─────────────────────────────────────────────────────────────
Repro 3: f-string 仅 ternary 无尾部 (td=1, jd=0)
─────────────────────────────────────────────────────────────
def test(direction):
    return f"{'IN' if direction == '0' else 'OUT'}"

反编译输出 (BUG):
def test(direction):
    return {'IN' if direction == '0' else 'OUT'}

Bug说明: f-string 被误解析为集合(set)字面量！
first_diff: FORMAT_VALUE((None, False)) → BUILD_SET(1)

反编译器无法识别 f-string 的引号和花括号嵌套结构，
将 {expr if cond else expr} 误认为是集合构造。

─────────────────────────────────────────────────────────────
Repro 4: f-string 双 ternary
─────────────────────────────────────────────────────────────
def test(x, y):
    return f"{'A' if x else 'B'}{'C' if y else 'D'}"

(此变体匹配 - 多个 ternary 反而正确，可能因为 BUILD_STRING(2)
提供了足够的结构线索)

─────────────────────────────────────────────────────────────
Repro 5: if-elif-else + kwargs + f-string ternary (完整截断模式)
─────────────────────────────────────────────────────────────
def transfer(self, direction, amount, exchange_type='1'):
    if exchange_type not in ('1', '2'):
        log.error(f'unsupported: {exchange_type}')
        return False
    elif direction not in ('0', '1'):
        log.error(f'unsupported: {direction}')
        return False
    else:
        kwargs = {'exchange_type': exchange_type, 'amount': amount, 'direction': direction}
        error_dict, response = self.broker.transfer(**kwargs)
        if error_dict.get('error_no') != 0:
            return f"{'转入' if direction == '0' else '转出'}极{'沪A' if exchange_type == '1' else '深A'}"
    return True

(此变体匹配 - 可能因为函数足够复杂，反编译器走了不同的代码路径)

═══════════════════════════════════════════════════════════════════
修复优先级总结
═══════════════════════════════════════════════════════════════════

优先级 1 (HIGH) - P_FOR_ELSE (9/19 = 47%)
  修复建议: 修复 while-else/for-else 的 else 子句识别。
  CPython 3.11 中 while 条件失败跳转到 else 体时，需要正确识别
  JUMP 目标是 else 块而非 while 后续代码。
  关键: 正确区分 "while 条件退出→else体" 和 "if 条件跳过→while 后续"
  
优先级 2 (HIGH) - P_FSTRING_TERNARY (3/19 = 16%)
  修复建议: 修复 f-string 中 ternary 表达式的重建。
  两个子bug:
  a) 单 ternary f-string 被误解析为集合字面量
  b) ternary 后的尾部文字被丢失
  关键: FORMAT_VALUE + BUILD_STRING 序列需要正确识别 f-string 边界

优先级 3 (MEDIUM) - P_TRY_EXCEPT (3/19 = 16%)
  修复建议: 修复 while+try/except 中 JUMP_FORWARD vs JUMP_BACKWARD
  边界识别。try 体结束的 JUMP_FORWARD 不应被误认为 while 回跳。

优先级 4 (MEDIUM) - P_COND_INVERT (2/19 = 11%)
  修复建议: 修复条件跳转方向反转问题。while 条件的 POP_JUMP_FORWARD_IF_TRUE
  不应被反转为 IF_FALSE（伴随 if/else 体交换）。

优先级 5 (LOW) - P_OTHER (2/19 = 11%)
  需进一步分析，可能也是 f-string / %-format 字符串重建问题。
"""

print(PATTERN_DETAILS)
print(MINIMAL_REPROS)

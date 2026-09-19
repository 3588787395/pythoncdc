# Round 2 — trade_info_utils.pyc 10 个不匹配函数根因分析与复现

日期：2026-09-19
目标文件：`site-packages/IQCommon/util/trade_info_utils.pyc`（40 函数，30 匹配 / 10 不匹配）
分析工具：
- `python _r2_dis.py <pyc> <func> [offset]` — 反汇编指定函数
- `python _r2_adiff.py <pyc> <OK.py> <func>` — difflib 对齐的原始指令序列 diff（忽略 EXTENDED_ARG/PRECALL/NOP/RESUME/CACHE）
- `python _r2_run_repro.py <repro.py>` — 复现流水线：py_compile → `pycdc --region` 反编译 → 重新编译 → `compare_bytecode` 比对（附 difflib raw_ratio）
- 区域管线调试：`core.cfg.build_cfg` + `RegionASTGenerator(cfg).generate()` 直接跑在单个 code object 上

**关键方法论**：对每个函数先做"原始指令序列 vs 重编译指令序列"的 difflib 对齐。
`raw_ratio=1.000` 表示反编译器输出逐字节完美，不匹配完全由比较器归一化规则造成；
`raw_ratio<1.0` 时首个非等 hunk 即反编译器真实缺陷。

---

## 1. 根因分类汇总表

| # | 函数 | orig→decomp (过滤后) | raw_ratio | 根因（一句话） | 算法阶段 | 严重度 |
|---|---|---|---|---|---|---|
| 1 | set_trade_status | 160→3 | 0.026 | while 内 try 内 with 体末尾有 `break`，触发 `_fold_break_to_return_w` 对 `'orelse': None` 的 If 节点 `len(None)` 崩溃，pycdc 捕获后整函数回退为 `pass` | 区域归约→AST生成（节点不变量违规）+异常回退策略 | 灾难（语义丢失） |
| 2 | check_and_update_trade | 218→207 | **1.000** | 反编译输出逐字节完美；比较器 `_remove_inlined_finally_in_except`(R104b) 单边从 decomp 剪掉 11 条指令（把"except 尾部 15 条指令内的 return-None 窗口"误判为内联 finally，窗口里其实是旋转 while 的循环回边） | 比较器（test harness），非反编译器 | 误报 |
| 3 | query_strategy_id | 103→97 | ~1.0（仅跳转目标互换） | 原始是 `if not exists: return None` 早退守卫 + try/except 尾部 `return None`（两个 return-None 块，守卫路径指向前者）；反编译器改写成 `if exists:` 包裹 + return 放进 if 内，两个等价 return-None 块的"被指向关系"互换（仅 jump 目标不同）；该尾部布局又触发 R104b 误剪产生 true_diffs | 代码生成（守卫重构/return 块布局）| 等价（语义无损） |
| 4 | query_trade_strategy_info | 109→103 | ~1.0（仅跳转目标互换） | 同 #3（614↔618 两个 return-None 块角色互换） | 同 #3 | 等价（语义无损） |
| 5 | get_trade_unit_info | 236→235 | 0.992 | finally 中 `if fp is not None: fp.close()` 被渲染成 `if not fp: fp.close()`（POP_JUMP_FORWARD_IF_NONE → POP_JUMP_FORWARD_IF_TRUE，丢失 is-None 比较；且生成代码语义错误：fp 为 None 时会对 None 调 close） | AST生成（条件渲染：NONE 类跳转误作真值取反）| 语义错误 |
| 6 | get_user_info | 96→110 | 0.810 | try/finally 内 for 循环中的 `return item`：CPython 编译为 `LOAD_FAST item; SWAP(2); POP_TOP`（返回值+丢弃循环迭代器）+ 内联 finally；反编译器误读为裸表达式语句 `item` + `if fp is not None: return fp.close() else: return None`（多出指令且返回值错误）；finally 同样被渲染成 `if not fp:` | AST生成（return-in-loop 的 SWAP(2) 迭代器清理模式）+ 条件渲染 | 语义错误 |
| 7 | kill_trade_process | 573→572 | 0.928 | 嵌套 if 被拍平提升：`if getsize==0: {log; rm; if len>0: body}` → `{log; rm}; if getsize==0 and len>0: body`——外层 if 体语句被提升到条件之前（副作用变为无条件执行），两个 if 条件被合并成 and；另有 if/else 分支块位置重排（等价） | 区域分类/区域归约（嵌套 if 合并 + 体提升）| 语义错误 |
| 8 | trade_operation | 304→282 | ~0.93 | (a) 循环尾本无 `continue`，反编译器额外生成一条，重编译出现两条连续 JUMP_BACKWARD（first_diff idx169 的直接原因）；(b) 内层 `with FileLock(delete_trade_list_file):` 从其 body 处脱落，body 语句升级，while 头部在 if/else 之后以死代码 `with FileLock(...): pass` 复活，BEFORE_WITH/PUSH_EXC_INFO/WITH_EXCEPT_START 指令簇丢失 | 区域分类（with 区域嵌套归约失败）+ AST生成（循环尾 continue）| 语义错误 |
| 9 | create_user_code_iqe | 834→832 | 0.896 | or 链被反演成 and 链（`bm is None or bm==B2 or reloads` → `bm is not None and bm==B2 or reloads and reloads`），内层 `if reloads:` 守卫被吸收进外层条件成为重复操作数，内层 if/else 拍平为两条顺序赋值（else 分支失去守卫），elif 的 `bm==B1` 操作数丢失只剩 `not reloads` | 区域归约（boolop 链重建 + 嵌套 if 吸收）+ AST生成 | 语义错误 |
| 10 | get_last_stat | 664→659 | 0.709 | 长下标链接收者在生成 append 语句时被截断：`result_data['data']['stat']['information']['value'].append(...)` → `'value'.append(...)`（LOAD_FAST + 3×LOAD_CONST/BINARY_SUBSCR 前缀整体丢失）；`([x] or [0])[0]` 表达式被掺入重复的三元式 | AST生成（下标接收者链重建）| 语义错误 |

比较器侧结论：10 个不匹配中，**check_and_update_trade 是纯比较器误报（raw_ratio=1.000）**；query_strategy_id / query_trade_strategy_info / get_trade_unit_info 的报告 first_diff（POP_EXCEPT vs LOAD_CONST）是 R104b 误剪后的级联伪差，其反编译器层面的真实差异分别是"return 块布局互换（等价）"与"finally is-None 条件误渲染（不等价）"。

---

## 2. 逐函数详细分析

### 2.1 set_trade_status（160 → 3，反编译为 `pass`）—— 灾难性结构 bug

原始结构（由字节码重建）：

```python
if os.path.exists(sim_trading_list_path):
    while count <= 3:
        try:
            with FileLock(sim_trading_list_path):
                file_io = FileIO(sim_trading_list_path)
                csv_reader = file_io.read(return_type='csv_reader')
                ...
                if len(write_info) > 0 and exchange_flag is True:
                    file_io.write(write_info, mode='w', data_type='list')
                break                 # ← 关键：with 体末尾的 break
        except BaseException:
            system_log.error(f'第{count}次设置交易状态失败，错误原因：{get_traceback_message()}')
            count += 1
else:
    system_log.error('%s文件不存在，无法修改交易状态' % sim_trading_list_path)
return exchange_flag
```

字节码证据（offsets 590-870）：

```
598 >> NOP
600-610  LOAD_CONST None×3; CALL        # FileLock.__exit__(None,None,None)
620      POP_TOP
622      JUMP_FORWARD to 868            # ← break：直达 868 return exchange_flag
624      PUSH_EXC_INFO                  # with 异常路径
...
646      JUMP_FORWARD to 806            # with 异常被抑制后回到 while 底部测试
...
794      POP_EXCEPT
796      JUMP_FORWARD to 806            # except 处理完回到 while 底部测试
806 >> LOAD_FAST count; COMPARE_OP <=
818      POP_JUMP_BACKWARD_IF_TRUE to 264  # 3.11 旋转 while 的底部回边
820 >> JUMP_FORWARD to 868
868 >> LOAD_FAST exchange_flag; RETURN_VALUE
```

**崩溃链（用 `RegionASTGenerator` 直接跑原始 code object 实测）**：

```
region_ast_generator.py:1506 generate → 2883 _generate_region → 10717 _generate_if
  → 13808 _if_generate_then_branch → 19456 _process_if_blocks → 2881 _generate_region
  → 3994 _generate_loop → 6021 _loop_generate_while
  → 6016 _fold_break_to_return_w (递归×3) → 6004: len(None) → TypeError
```

1. while 的 LoopRegion `has_break=True`（breaks=[622]，即 with 清理后的 break 跳块）；
2. `_loop_generate_while` 走 break 折叠分支，调用 `_fold_break_to_return_w(body_stmts)`；
3. 该助手 `s.get('orelse', [])` 后直接 `len(_orelse)`，但循环体 If 发射点（region_ast_generator.py 行 7426、7433、8840、8861、8868、31296、35508）会生成 `'orelse': None` 的 If 节点（键存在值为 None，`.get` 默认值失效）→ `TypeError: object of type 'NoneType' has no len()`；
4. `pycdc.py` 的 region 路径 `except Exception` 捕获后对该函数整体回退，最终输出 `pass`。

对照实验：同一骨架去掉 with 体末尾的 `break`（probe_pair2）→ 16 区域、`has_break=False`、完全匹配；加回 `break`（probe_pair3 / r2_01）→ orig=155~160, decomp=3, first_diff idx1 `LOAD_CONST(1) vs LOAD_CONST(None)`，与目标函数完全同签名。更小的 `while+try+with+break`（r2_11）不塌缩但结构错位（`LOAD_CONST(None)` vs `CALL(2)`）——说明崩溃需要 break 折叠路径 + 内层 If(orelse=None) 节点同时存在。

### 2.2 check_and_update_trade —— 反编译器无错，比较器 R104b 误报

`difflib.SequenceMatcher(None, orig_instrs, decomp_instrs).ratio() == 1.000`（217 条含跳转目标完全一致），**反编译输出重新编译后与原始 pyc 逐字节相同**。

报告的 13 条 true_diffs 全部来自 `testqouter/round1/base.py` 的 `_remove_inlined_finally_in_except`（R104b）：它在 decomp 一侧找到 except handler 的 POP_TOP（前置 CHECK_EXC_MATCH/POP_JUMP），再找其后的 POP_EXCEPT，然后向后扫描 ≤15 条指令寻找 `LOAD_CONST+RETURN_VALUE`，把窗口整体删除（本例删除 11 条：POP_EXCEPT, JUMP_FORWARD, RERAISE, COPY, POP_EXCEPT, RERAISE, LOAD_FAST count, LOAD_CONST 3, COMPARE_OP <, POP_JUMP_BACKWARD_IF_TRUE, JUMP_BACKWARD）。该窗口实际是**旋转 while 的底部条件回边 + 循环退出的隐式 return-None 块**，不是内联 finally。R104b 是单边修剪（只改 decomp 不校验 orig 同位置结构），原始函数的 except 尾部 + while 底部测试 + return-None 落在 15 条窗口内即触发。

原始尾部布局（offsets 1326-1358）：

```
1326 POP_EXCEPT                        # handler 正常出口
1328 JUMP_FORWARD to 1338
1330 RERAISE / 1332 COPY / 1334 POP_EXCEPT / 1336 RERAISE   # 死清理块
1338 LOAD_FAST count; COMPARE_OP <
1348 POP_JUMP_BACKWARD_IF_TRUE to 30   # while 底部回边
1352 JUMP_BACKWARD to 6                # 外层 for 回边
1356 LOAD_CONST None; RETURN_VALUE     # ← 15 条窗口内的 return-None 触发 R104b
```

### 2.3 query_strategy_id / query_trade_strategy_info —— 早退守卫重构导致 return 块布局互换（等价）

两函数原始序列与重编译序列的 difflib 对齐结果：**唯一差异是跳转目标**。以 query_strategy_id 为例（query_trade_strategy_info 同构，614↔618）：

```
orig : 196 POP_JUMP_FORWARD_IF_FALSE → 644   # exists==False 路径
orig : 634 JUMP_FORWARD → 648                # except handler 出口
块 644: LOAD_CONST None; RETURN_VALUE        # ← 守卫早退 return（布局在前）
块 648: LOAD_CONST None; RETURN_VALUE        # ← try/except 后 return（布局在后）

decomp: 196 POP_JUMP_FORWARD_IF_FALSE → 648  # 指向函数末尾隐式 return
decomp: 634 JUMP_FORWARD → 644               # 指向 after-try return
```

即：原始源码是 `if not os.path.exists(p): return None` 早退守卫 + try/except 之后的 `return None`（CPython 为两条路径生成两个独立 return-None 块，守卫块在前）；反编译器改写成 `if os.path.exists(p): try/except ... return None`（守卫路径落到函数末尾隐式 return，after-try return 在前），两个语义等价的块角色互换。反编译输出本身语义无损；差异仅 jump 目标，本应按 R35 记为 jump_only（匹配），但 R104b 对 decomp 的 6 条误剪把它变成了 true_diffs。

### 2.4 get_trade_unit_info —— finally 的 is-None 比较被渲染成真值取反

原始 offsets 1296-1342（try/except/finally 是 for 循环体最后一条语句）：

```
1296    LOAD_FAST fp
1298    POP_JUMP_FORWARD_IF_NONE to 1340   # fp 为 None → 跳过 close（回循环）
1300-1338  fp.close()
1340 >> JUMP_BACKWARD to 94               # NONE 跳转目标 = for 循环回边
```

反编译 OK.py 输出：

```python
finally:
    if not fp:        # ← POP_JUMP_FORWARD_IF_TRUE；应为 `if fp is not None:`
        fp.close()
```

NONE 类条件跳转被映射为真值取反（`not fp`），丢失 `is None` 语义；重编译为 POP_JUMP_FORWARD_IF_TRUE，与 orig 的 POP_JUMP_FORWARD_IF_NONE 形成真差异，并导致后续 finally 双份（正常路径 + PUSH_EXC_INFO 异常路径，offsets 1344-1392）对齐错位。报告的 first_diff idx104（POP_EXCEPT vs LOAD_CONST）是 R104b 误剪后的级联位置，真实第一差异是 NONE↔TRUE 跳转互换。

### 2.5 get_user_info —— try/finally 内循环中的 return 的 SWAP(2) 迭代器清理被误读

原始 offsets 214-266：

```
214-266（for 循环体内，try/finally 区域）:
212 POP_JUMP_FORWARD_IF_FALSE to 268      # if item[0] == trade_id
214 LOAD_FAST item                        # 返回值
216 SWAP(2)                               # 与栈上循环迭代器交换
218 POP_TOP                               # 丢弃迭代器
220 LOAD_FAST fp
222 POP_JUMP_FORWARD_IF_NONE to 266       # 内联 finally: if fp is not None
224-262 fp.close()
264 RETURN_VALUE                          # return item
266 RETURN_VALUE                          # fp 为 None 时直接 return item
```

这是 CPython 3.11 对"try/finally（finally 被内联到 return 路径）内的 for 循环中 `return <var>`"的编译形态：返回值入栈 → SWAP(2)+POP_TOP 弹掉迭代器 → 内联 finally → RETURN_VALUE。

反编译 OK.py 输出（语义错误）：

```python
if item[0] == trade_id:
    item                    # ← 返回值被降级为裸表达式语句
    if fp is not None:
        return fp.close()   # ← 返回 None（close 的返回值），不是 item
    else:
        return None
...
finally:
    if not fp:              # ← 同 2.4 的 is-None 误渲染
        fp.close()
```

SWAP(2)+POP_TOP 迭代器清理未被识别为 return 的一部分；内联 finally 的 close+RETURN 被改造成 if/else 双 return；finally 条件再次丢 is-None。raw 序列 95 vs 115（decomp 多 20 条），first_diff idx40 SWAP(2) vs POP_TOP。

### 2.6 kill_trade_process —— 嵌套 if 拍平：体提升 + 条件合并

原始 offsets 954-1232（except BaseException 处理器内）：

```
954-1024  os.path.getsize(sim_trading_path)==0 → POP_JUMP_FORWARD_IF_FALSE to 2614
1026-1114    app_log.warning('用户{}{}文件大小为空，执行删除操作'...)   ← 外层 if 体
1116-1192    os.system('sudo rm -rf {}'.format(...))                  ← 外层 if 体
1194-1232  len(trade_id_list)>0 → POP_JUMP_FORWARD_IF_FALSE to 2614
1234+        app_log.info('...重新生成{}文件'...)                      ← 内层 if 体
```

即 `if getsize==0: {log; rm; if len>0: regen}`（两个 if 的 False 目标同为 2614）。
反编译 OK.py：

```python
app_log.warning('用户{}{}文件大小为空，执行删除操作'...)   # ← 提升到 if 外（无条件执行）
os.system('sudo rm -rf {}'.format(sim_trading_path))       # ← 同上
if os.path.getsize(sim_trading_path) == 0 and len(trade_id_list) > 0:   # ← 条件合并
    app_log.info('...重新生成...')
```

外层 if 体语句被提升出条件（getsize!=0 时也会 log+rm，副作用语义改变），两个 if 合并为 and。first_diff idx138（LOAD_GLOBAL os vs LOAD_GLOBAL app_log）即该块位置对调所致。另一处 hunk（orig[301:312] 删除 / decomp[330:340] 插入）是 `if len(response)>0: {...} else: {log; continue}` 与顺排 `if ...: {...continue}; log; continue` 的等价布局差异。

### 2.7 trade_operation —— with 区域脱落 + 循环尾多余 continue

**(a) 多余 JUMP_BACKWARD**（first_diff idx169 的直接来源）：orig 循环尾只有一条 `JUMP_BACKWARD to 654`；decomp 在 `write_info.append(items)` 后多生成了显式 `continue`（OK.py 第 42 行），重编译后出现两条连续 JUMP_BACKWARD。

**(b) with 脱落**：原始中 `with FileLock(delete_trade_list_file):` 包裹 `FileIO(...).write(delete_write_info, ...)`（存在 FileLock CALL+BEFORE_WITH+POP_TOP 与退出簇 PUSH_EXC_INFO/WITH_EXCEPT_START/None×3 CALL）。反编译输出：

```python
if len(delete_write_info) > 0:
    mode = 'w' if new_file_flag else 'a'
    FileIO(delete_trade_list_file).write(delete_write_info, mode=mode, data_type='list')  # ← 无锁
...
    with FileLock(delete_trade_list_file):   # ← 死代码复活在 if/else 之后
        pass
```

with 头与其 body 分离：body 语句脱离锁作用域（语义错误），with 头在不可达位置以 `with: pass` 复活。

### 2.8 create_user_code_iqe —— or→and 反演、嵌套 if 吸收、if/else 拍平

原始 offsets 2734-2906（函数级 if/elif 链）：

```
2734 LOAD_FAST business_mode
2736 POP_JUMP_FORWARD_IF_NONE to 2766        # A: bm is None（真→2766）
2738-2758 COMPARE_OP ==; POP_JUMP_FORWARD_IF_TRUE to 2766    # B: bm == B2（真→2766）
2760 LOAD_FAST reloads
2764 POP_JUMP_FORWARD_IF_FALSE to 3698       # C: reloads（假→3698=elif 路径）
2766 >> LOAD_FAST reloads                    # 内层 if reloads:
2768 POP_JUMP_FORWARD_IF_FALSE to 2904       #   假→2904（else: 'user_strategy'）
2770-2900   tmp=int(time.time()); strategy_file_name='user_strategy_...'
2902 JUMP_FORWARD to 2908
2904 >> LOAD_CONST 'user_strategy'; STORE_FAST strategy_file_name
2908 >> strategy_file = os.path.join(...)
...
3698 >> LOAD_FAST business_mode; COMPARE_OP ==  # elif business_mode == B1
3720 POP_JUMP_FORWARD_IF_FALSE to 4438
3722 LOAD_FAST reloads; POP_JUMP_FORWARD_IF_TRUE to 4438   # and not reloads
```

源码：`if bm is None or bm == B2 or reloads: { if reloads: X else: Y; Z } elif bm == B1 and not reloads: W`。
反编译 OK.py：

```python
if business_mode is not None and business_mode == BUSINESS_MODE_2 or reloads and reloads:
    tmp = int(time.time())
    strategy_file_name = 'user_strategy_{}'.format(str(tmp))
    strategy_file_name = 'user_strategy'          # ← else 拍平成顺序赋值
    ...
if not reloads:                                    # ← elif 丢失 bm==B1 操作数
    src_so_path = ...
```

四处畸变：or 首操作数反演（is None→is not None、or→and）、内层 `if reloads:` 被吸收为重复的 `and reloads`、内层 if/else 拍平（else 赋值失去守卫，JUMP_FORWARD to 2908 消失 → first_diff idx550 JUMP_FORWARD(2908) vs LOAD_CONST('user_strategy')）、elif 条件截断。

### 2.9 get_last_stat —— 下标接收者链截断

原始（filtered seq idx 476-488）：

```
479 LOAD_FAST result_data
480 LOAD_CONST 'data';  BINARY_SUBSCR
482 LOAD_CONST 'stat';  BINARY_SUBSCR
484 LOAD_CONST 'information'; BINARY_SUBSCR
486 LOAD_CONST 'value'; BINARY_SUBSCR
488 LOAD_METHOD append
```

反编译 OK.py 第 53 行：

```python
'value'.append(([item[12 + index]] or [0] if item[12 + index] else [0])[0])
```

`result_data['data']['stat']['information']` 四级接收者前缀整体丢失（只剩字符串字面量 `'value'`）；`([x] or [0])[0]` 被掺入重复条件的伪三元式。这是 10 个不匹配中指令数差距最大的真实语义丢失之一。

### 2.10 环境备注（非根因）

原始 pyc 由较旧的 3.11.x 编译：全局接收者的方法调用编译为 `LOAD_GLOBAL(NULL flag)+LOAD_ATTR+CALL`，本地 Python 3.11.7 编译为 `LOAD_GLOBAL+LOAD_METHOD+CALL`。比较器 R34（base.py:911）已将 LOAD_ATTR/LOAD_METHOD 等同处理，因此不构成上述任何不匹配的原因，但分析原始序列时需注意。

---

## 3. 复现实例（test_repros/round2/）

验证方式：`python _r2_run_repro.py <repro.py> [func]`（py_compile → `pycdc --region` → 重编译 → `compare_bytecode`）。
**11/11 全部复现成功**；每个文件 ≤60 行、独立可编译、只含触发结构。

| 文件 | 对应根因（章节） | 目标函数 | 验证结果（关键签名） |
|---|---|---|---|
| r2_01_set_trade_status_collapse.py | §2.1 while+try+with 内 break → orelse=None 崩溃 → `pass` | set_trade_status | **复现成功**：orig=155 decomp=3，idx1 LOAD_CONST(1) vs LOAD_CONST(None)（与目标函数同签名） |
| r2_02_guard_early_return.py | §2.3 早退守卫 `if not exists: return None` 重排 return 块 | query_strategy_id / query_trade_strategy_info | **复现成功**：orig=90 decomp=89，idx65 LOAD_CONST(None) vs JUMP_FORWARD(504)（尾部 return 块互换） |
| r2_03_finally_is_not_none.py | §2.4 循环体末 try/except/finally 的 `if fp is not None` → `if not fp` | get_trade_unit_info | **复现成功**：orig=234 decomp=233，idx104 POP_EXCEPT vs LOAD_CONST（与目标函数 first_diff 同位同型）；dec 输出确认含 `if not fp:` |
| r2_04_return_in_loop_finally.py | §2.5 try/finally 内循环中 `return item` 的 SWAP(2) 模式 | get_user_info | **复现成功**：orig=78 decomp=92，idx22 SWAP(2) vs POP_TOP（与目标函数同型） |
| r2_05_nested_if_merge.py | §2.6 嵌套 if 拍平/体提升/条件合并 | kill_trade_process | **复现成功**：orig=67 decomp=61，idx12 LOAD_GLOBAL(os) vs LOAD_GLOBAL(_app_log)（if 体提升，与目标函数同型） |
| r2_06_subscript_chain_truncate.py | §2.9 下标接收者链截断 | get_last_stat | **复现成功**：orig=82 decomp=47，idx34 LOAD_FAST(result_data) vs LOAD_FAST(item)（接收者链丢失） |
| r2_07_with_lock_dropped.py | §2.7(b) with 头与 body 分离、死 `with: pass` | trade_operation | **复现成功**：orig=63 decomp=32，idx24 LOAD_GLOBAL(FileLock) vs LOAD_CONST(True)（with 指令簇丢失） |
| r2_08_loop_tail_branches.py | §2.7(a) 循环尾多余 continue → 重复 JUMP_BACKWARD | trade_operation | **复现成功**：orig=121 decomp=122，idx82 LOAD_CONST(None) vs JUMP_BACKWARD(80) |
| r2_09_bool_cond_invert.py | §2.8 or→and 反演 + elif 吸收 + if/else 拍平 | create_user_code_iqe | **复现成功**：orig=93 decomp=92，idx4 PJ_NONE vs PJ_TRUE、idx26 JUMP_FORWARD(178) vs LOAD_CONST(user_strategy)（与目标函数同型） |
| r2_10_except_tail_loop_cond.py | §2.2 while+try/except 尾部窗口触发比较器 R104b（反编译器本身无错） | check_and_update_trade | **复现成功（raw_ratio=1.000）**：原始序列逐字节一致仍报 12 条 true_diffs，idx56 POP_EXCEPT vs LOAD_CONST——纯比较器伪差 |
| r2_11_minimal_with_break.py | §2.1 的 12 指令最小核（不塌缩但结构错位） | （r2_01 家族最小化） | **复现成功**：orig=55 decomp=55，idx16 LOAD_CONST(None) vs CALL(2) |

失败/说明记录：
- r2_03 前两个版本（finally-if 不在循环体末位 / 缺少第一段 try/except+return None）反编译正确，未复现——触发条件确认为"finally-if 的 NONE 跳转目标恰为循环回边 + 前置完整 try/except 结构"。
- r2_09 第一版（无 elif 链、无后续语句）仅 jump_only 差异（判为匹配），未复现——需要 if/elif 链与内层 if/else 组合。
- r2_08 第一版（for 循环不在 if→try→with 内）反编译正确，未复现。
- 排除的干扰项：全局方法调用的 LOAD_ATTR/LOAD_METHOD 差异为编译器小版本差异，比较器 R34 已归一，未列为根因。

---

## 4. 修复建议（按优先级，均为算法级，禁止特判补丁）

**P0-1（一次修复 #1/#8 类，收益最大）：AST 节点不变量 + 防御性遍历**
`core/cfg/region_ast_generator.py` 中 7 处 If 发射点（行 7426/7433/8840/8861/8868/31296/35508）生成 `'orelse': None`，违反"分支节点 body/orelse 必须为 list"的隐式不变量；消费端 `_fold_break_to_return_w`(行 ~6004) 等遍历器用 `s.get('orelse', [])` 后直接 `len()`。修复：发射点统一改为 `'orelse': []`；同时在所有语句遍历器入口做 None→[] 归一（或提供统一的 `children(stmts)` 访问助手）。此外建议把"区域生成抛异常→整函数 `pass`"的回退（pycdc.py region 路径）改为"回退到该函数的 CFG 线性兜底输出"或至少逐语句降级，避免单点崩溃抹掉整个函数。

**P0-2（一次修复 #2/#3/#4 及 #5 的报告失真）：比较器 R104b 对称化**
`testqouter/round1/base.py` 的 `_remove_inlined_finally_in_except` 是单边修剪，不校验 orig 同位置结构。修复：仅当 decomp 在 [POP_EXCEPT, LOAD_CONST+RETURN_VALUE) 窗口内为纯直线代码（无任何 jump 指令——内联 finally 的特征）且 orig 同位置无该 POP_EXCEPT 时才修剪；或者反向：当 orig 与 decomp 在同位置具有相同 POP_EXCEPT 尾部时禁止修剪。R104b 当前误伤所有"except 处理器尾部 15 条指令内出现 return-None"的函数。

**P1-1（修复 #9 与 #7 的条件畸变）：boolop 链重建的收敛性校验 + 禁止体提升**
区域归约在重建 and/or 链时应使用可验证的不变量：真实 `and`/`or` 链的所有短路目标必须收敛到同一后继块（原始字节码中可直接验证）；不满足收敛性时不得合并操作数。`if A: S; if B: T` 只允许在 S 为空时折叠为 `if A and B: T`——任何把非空 if 体提升到条件之前的变换（#7 的 log/rm 提升）都改变副作用语义，必须禁止。elif 链重建需保留每个 elif 分支的完整守卫表达式（#9 丢失 `bm==B1` 操作数）。

**P1-2（修复 #5/#6 的条件畸变）：NONE 类条件跳转保真渲染**
条件渲染器遇到 POP_JUMP_FORWARD_IF_NONE / IF_NOT_NONE（以及对应 BACKWARD 变体）必须输出 `x is None` / `x is not None`（跳转方向取反时用 not-in 方言），任何"条件取反"变换不得把 None 比较降级为真值测试。该修复同时消除生成代码的 AttributeError 隐患（对 None 调 close）。

**P1-3（修复 #6 与 #8a）：return-in-loop 与循环尾 continue 的规范化**
(a) 识别 3.11 的 `LOAD_* <value>; SWAP(2); POP_TOP`（返回值+丢弃循环迭代器）序列，与后续内联 finally 合成 `return <value>`，禁止把返回值降级为表达式语句或在退出路径上伪造 if/else return；(b) 循环体最后一个语句之后不得再生成显式 `continue`——当区域的 continue 边与自然回边重合（同目标块）时合并为单条回边。

**P2-1（修复 #10）：下标接收者链完整性校验**
生成 `X.attr(...)`/`X[k](...)` 调用语句时，接收者的 LOAD_FAST/BINARY_SUBSCR 前缀必须与区域指令序列完整对齐；建议在 AST 生成后加一致性检查：Call 节点的 func 链所引用的指令跨度应连续覆盖原区域（本例原区域以 LOAD_FAST result_data 开始，而生成物以 LOAD_CONST 'value' 开始，跨度检查会立即失败并回退到保守渲染）。

**P2-2（修复 #8b）：with 区域原子归约**
WithRegion 归约必须保证 header/body/exit 三者一起生成：body 块不能脱离 with 作用域升级到外层，header 不得在 body 被 elsewhere 消费后以 `with: pass` 复活。可加不变量：生成的 With 节点必须认领其 BEFORE_WITH 所在块及其异常表块；含 `pass` 体的 With 节点若不在原 CFG 对应位置即为归约失败信号。

**P3（#3/#4，布局级）：早退守卫布局保持**
当原 CFG 中条件跳转的 False/None 目标块以 RETURN 结尾且区域出口与之汇合时，优先输出 `if not cond: return X` 早退守卫（而非 `if cond:` 包裹），使 CPython 重新生成相同的 return 块布局。此项为纯布局优化（当前输出语义已等价），优先级最低。

---

## 附：本文引用的关键产物

- 目标函数反汇编：`python _r2_dis.py site-packages/IQCommon/util/trade_info_utils.pyc <func>`
- 对齐 diff：`python _r2_adiff.py site-packages/IQCommon/util/trade_info_utils.pyc _r2_out/trade_info_utilsOK.py <func>`
- 复现验证：`python _r2_run_repro.py test_repros/round2/r2_XX_*.py [func]`
- 区域管线调试参考：`core/cfg/region_ast_generator.py` 行 6004/6021（崩溃点）、7426/7433/8840/8861/8868/31296/35508（orelse=None 发射点）；`testqouter/round1/base.py` `_remove_inlined_finally_in_except`（R104b，行 ~713）、R34（行 911）

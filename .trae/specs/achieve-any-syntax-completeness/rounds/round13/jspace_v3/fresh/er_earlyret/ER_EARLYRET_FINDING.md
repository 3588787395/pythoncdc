# while-True 循环头早返回守卫条件极性反转（rr-v5r89）

状态：**已修复**（`region_ast_generator.py` 循环头手写 if-break/return 路径
+34 行，只增不破）。真实案例形态：REAL46-003 `_c3_merge` 的
`if not sequences: return result` 早返回守卫。修复前 er3/er4 最小复现把
`if not items: return` **真反转**为 `if items: return/break`（语义错误）；
修复后与源逐字一致。

## 缺陷

`while True:` 循环头以条件跳转结尾、一臂是 return 的形态，手写重建路径
（`region_ast_generator.py` 12616-12700）直接把 return 臂当 then 分支发射
`if <test>: return`，未处理两件事：

1. **条件跳转极性**：CPython 3.11 对 `if not cond: <臂>` 做跳转翻转——
   编译为 `LOAD cond; POP_JUMP_IF_TRUE(跳过臂)`。旧路径不看跳转极性，
   把「条件为假时执行的 return 臂」发成 then 分支 → `if items: return`
   （条件取反，语义错误）。
2. **return-None 降级**：`LOAD_CONST None; RETURN_VALUE` 臂因
   `argval is not None` 守卫不回收返回值，被降级发射为 `break`
   （er3：`if not items: return None` → `if items: break`，极性与语义双错）。

```python
# 源
while True:
    if not items:
        return result
    result.append(items[0])
    items = items[1:]
# HEAD 产物（极性反转）
while True:
    if items:
        return result        # ← 条件反了：items 非空时 return
    result.append(items[0])
    items = items[1:]
```

## 根因（探针实证）

`er4_probe.py`：LoopRegion blocks=[(8,10) 头, (12,14) return 臂, (16,90) 体]。
头块尾指令 `POP_FORWARD_IF_TRUE (to 16)`——跳过 return 臂，即 return 在
**条件为假**时执行。手写路径 `_return_val` 回收成功后直接
`If(test=test_expr, body=[Return])`，test 未经极性调整。

触发边界（`er_variants.py` 四形态隔离）：
- er3/er4（循环头平铺语句体 + 早返回守卫）：极性真反转 → 本族缺陷；
- er1（守卫后体以 for 循环开头）：走 IfRegion 结构反转路径，产出
  `if cond: <体> else: return`——语义等价，独立登记非本族；
- er2（非循环的普通 if 早返回）：走通用 IfRegion 路径，仅多 `else`，
  语义等价，不受影响。

## 修复（只增不破，+34 行）

1. **极性判定**（结构事实，无名字/偏移特例）：条件跳转指令 `argval`
   即跳转目标块偏移——return/break 臂块偏移 == 跳转目标 ⟶ 臂在 test
   为真时执行（不反转），否则臂在 test 为假时执行（test 前加 Not）。
   仅对 `POP_JUMP_FORWARD/BACKWARD_IF_TRUE/IF_FALSE` 判定，其余跳转
   形态维持旧行为（C3）。Not 用小写 `'op': 'not'`（`ast_converter`
   op_map 只认小写；`code_generator` 同样接受）。
2. **return-None 保留**：`LOAD_CONST None` 臂且块含 RETURN_VALUE 且非
   模块级时回收 `Constant(None)` 返回值——break 在字节码中是
   JUMP_FORWARD 不含 RETURN_VALUE，故该臂只可能是真实 `return None`。

## 验证（实测读数）

| 检查 | 修复前 | 修复后 |
|---|---|---|
| er3 repro（`if not items: return None`） | `if items: break`（极性+语义双错） | **`if not items: return None`**，与源逐字一致 |
| er4 repro（`if not items: return result`） | `if items: return result`（极性反） | **`if not items: return result`**，与源逐字一致 |
| er1（IfRegion 结构反转） | `if sequences: ... else: return` | 不变（语义等价，非本族） |
| er2（普通 if 早返回） | `if not sequences: ... else:` | 不变（语义等价） |
| SWAP 中段族回归（rr-v5r88） | — | x1/el1/y1 中段语句全在 |
| el_variants 6 / el_narrow 8 | — | 6/6 MISSING none、8/8 无 LOST |
| varargs 注解回归（rr-v5r87） | — | ann_repro 三函数注解全在、va_variants 8/8 |
| 三元/if-早返回/Ellipsis 回归 | — | 全绿 |
| REAL46-003 / REAL46-031 R7 | 4 / 2 | 4 / 2（不变——er1 形态走 IfRegion 反转路径，语义等价独立子族） |
| pytest 7 文件 | 2 failed / 282 passed / 2 xpassed（既有） | **零新增失败** |
| 全量 1556 闸门 | 基线 v5r88 shard json | 见下节 |

## 全量 1556 闸门（对 v5r88 基线）

实测读数（`semantic_shard{0,1,2}_v5r89.json` vs `..._v5r88.json`）：

- 基线 verdicts：`{'EQUAL': 1132, 'ERROR': 423, None: 1}`；本轮：`{'EQUAL': 1132, 'ERROR': 423, None: 1}`（逐字相同）
- **REGRESSION（EQUAL→非EQUAL）：0**；IMPROVEMENT：0
- 唯二变化 `JS-IF-066 None→ERROR`、`JS-IF-074 ERROR→None`：均为产物加载/执行失败类记录在两个互斥状态间的抖动（同 v5r86/v5r88 轮已登记情形），EQUAL 计数不变，非回归。

## 诚实边界

- er1 形态（守卫后循环体以 for/嵌套结构开头）走 IfRegion 结构反转路径，
  产出 `if cond: <body> else: return`——语义等价但 AST 形态与源不同，
  REAL46-003 v[51] `_c3_merge` R7 差属此独立子族，**登记未修**。
- 不宣称 G2c 通过（REAL46-004 use_args 60 差观察层在案）；
  `product_complete` 仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `er3_guardsimple.py` + `er3_guardsimple_decompiled.py` | 极性反转+return-None 降级复现（修复后产物） |
| `er4_guardappend.py` + `er4_guardappend_decompiled.py` | 极性反转复现（修复后产物） |
| `er1_c3merge.py` / `er2_plainguard.py` + decompiled | 等价形态边界（不受影响） |
| `er_variants.py` | 四形态变体矩阵 |
| `er4_probe.py` | LoopRegion 块结构探针 |
| `apply_erfix.py` / `fix_not_op.py` | 精确替换应用脚本（CRLF 安全） |
| `fix_patch.diff` | 完整修复 diff（含判据注释） |


---

# rr-v5r95：v[51] `_c3_merge` IfRegion 结构反转完整修复（[v51-ERGUARD]，Task 21）

## 根因（er1 区域树 + settrace 实证）

er1 区域树：`LoopRegion@8 blocks=[8,36,40,...] while_true=True cond=None`——
头部守卫 **无 IfRegion**（B36 return 臂、B40 for 延续臂均 LOOP_BODY 角色，
不进 exit 后继分类）→ 发射走 `_loop_handle_no_exit_successors`（settrace 实证
唯一命中 L16641）。旧路径按 `_is_if_false` 定 then/else 后一律走
L16641 `If(test, body=延续, orelse=[return])`——对 CPython 早返回守卫的
跳转翻转布局（**跳转目标=延续块、落空臂=纯 return 块**）产生结构反转
`if cond: <for> else: return result`。

姊妹方法 `_loop_handle_exit_successors`（L16111-16129）对 RETURN 角色块
早已发射早返回形式；本族 return 臂角色停留 LOOP_BODY 使其不可达——
同一发射语义在 no-exit 路径缺失，即本族根因。

## 修复（只增不破，+65 行）

`_loop_handle_no_exit_successors` 在两纯 continue 早退分支之后、
R21-33c2 之前插入 `[v51-ERGUARD]` 分支。判据（全部结构事实）：
1. 落空臂 `_fall_through` 不含任何跳转类指令（FORWARD/BACKWARD_JUMP +
   FORWARD/BACKWARD_CONDITIONAL）且以 RETURN_VALUE/RETURN_CONST 终止；
2. 两臂均非 continue 目标/纯 continue（continue 形态交由上方既有分支，C3）；
3. 跳转 op 为 IF_TRUE/IF_FALSE（IF_NONE/OR_POP 形态维持旧路径）。

发射：`if [not] cond: return X` + 延续臂（区域入口优先生成）顺序跟随。
极性（er-POL 同口径结构事实版）：op 含 IF_FALSE ⟹ 延续在假臂 ⟹ return
臂在真臂（test 不取反）；含 IF_TRUE ⟹ 取反。跳转目标=return 臂的布局
（源 `if cond: <体> else: return`）不满足判据①，维持旧结构发射（C3）。

## 验证（全实测）

| 检查 | 修复前（v5r94） | 修复后（v5r95） |
|---|---|---|
| er1 产品形态 | `if sequences: <for> else: return result` | **`if not sequences: return result` + for 顺序跟随** |
| er1 co_code+异常表（全 code object） | co_code DIFF | **BYTE-EQUAL** |
| er_variants 四形态字节 | er1 DIFF、er2/3/4 EQ | **4/4 BYTE-EQUAL** |
| REAL46-003 `_c3_merge`（v[51]） | co_code DIFF（唯一 R7 阻塞） | **BYTE-EQUAL** |
| 权威 semantic_diff（v6 基线复测） | DIFFERENT，唯一 diff `R7 $.metadata.code.co_consts.v[51].code_sha` | **EQUAL, diffs=[]**（仅 3 项标准容忍） |
| REAL46 全量 46 sweep | 17 DIFFERENT / 12 EQUAL | **16 DIFFERENT / 13 EQUAL**，唯一变化 003 DIFFERENT→EQUAL，**0 回归** |
| REAL46-003 全函数字节（v6 vs v7 对照） | 27 函数差（4 co_code + 23 consts 噪声） | removed=[_c3_merge co_code]，added=[]（4 co_code 为既有登记子族） |
| 20 形态矩阵（fe m2-m5/fe1、te s1-s5、te_variants v1-v8、w28 w1/w3/w4） | BYTE-EQUAL | 全部不变（w2 不可达 continue 既有丢弃形态逐字不变） |
| 前轮探针（el1/y1/x1/r31/ann/tern/ell/fi1 重反编译） | BYTE-EQUAL | 全部 BYTE-EQUAL 且文本与上轮记录一致（tern `<module>` 为既有登记差） |
| pytest 7 套件 | 2 failed / 282 passed / 2 xpassed（冻结对） | **一致，零新增** |
| 比较器冻结 | pyc_verify.py SHA256 FE1902...DFF4 | **一致，tests/pyc_verify 零改动** |
| 全量 1556 闸门（对 v5r89 基线） | 见下节 | 见下节 |

## 诚实边界

- REAL46-003 内 4 个函数级 co_code 差（`_lru_cache_wrapper.cache_clear`、
  `wrapper`、`partial.__reduce__`、`__setstate__`）为 v6 既有（该 4 差在
  semantic_diff 的模块级 R7 口径下不构成 case 阻塞，v6 复测唯一 diff 即
  v[51]），**登记为独立子族**，本轮不动。
- 不宣称 G2c 通过（REAL46-004 use_args BoolOp 重叠层 60 差在案；
  46 sweep 另有 16 DIFFERENT / 17 ERROR）；`product_complete` 仍 **NOT PASS**。

## 证据（本目录新增）

| 文件 | 作用 |
|---|---|
| `fix_patch_v5r95.diff` | [v51-ERGUARD] 完整 diff（+65 行含判据注释） |
| `REAL46-003_product_v5r95.py` | v7 产品（唯一文本变化即 v[51] 修复） |
| `case_r003_v7.json` / `semantic_r003_v7.json` | 权威 semantic_diff 整案 EQUAL |
| `case_r003_v6_baseline.json` / `semantic_r003_v6_baseline.json` | v6 基线 DIFFERENT 复测（唯一 diff = v[51] code_sha） |
| `er1_out_v5r95.py` | er1 修复后产品 |
| `v51_bytecompare.py` | 逐 code object 字节比对 harness |


## 全量 1556 闸门（对 v5r89 基线，semantic_shard{0,1,2}_v5r95.json）

- 基线 verdicts：`{'EQUAL': 1132, 'ERROR': 423, None: 1}`；本轮：`{'EQUAL': 1180, 'ERROR': 376, None: 0}`
- **REGRESSION（EQUAL→非EQUAL）：0**
- IMPROVEMENT（ERROR→EQUAL）：**48**（JS-TRY-002/011/012/013/014/016/030/031/032/034/036/039、JS-IMPORT-002/003/008-014/016/017/019、JS-WITH-003/012/015/018/019/021-024/026/027/030、JS-ANNASSIGN-001/003-013）
- OTHER：1（JS-IF-074 None→ERROR，同 v5r94 轮已登记的加载抖动）

### 48 案改善的归因（全实测，非 [v51-ERGUARD] 单点功效——诚实边界）

1. 48 案的 c4 错误均为 `original artifact did not load/execute`（**原件侧**加载失败，与产品无关），且自 v5r79 起六轮（79/89/90/92/94）读数恒 ERROR——即这 48 案历史上**从未被测量**（original 加载失败短路，product 从未进入判定）。
2. 本轮原件加载成功。抽样 4 案（JS-TRY-002/JS-IMPORT-002/JS-WITH-003/JS-ANNASSIGN-001）独立复跑 semantic_diff 均 EQUAL（判定可复现）。
3. **A/B 归因**：git show HEAD 版 region_ast_generator.py 文件交换复算 4 案产品，与本轮闸门产品**逐字节一致**（HEAD 为未含 [v51-ERGUARD] 的已提交态）→ 48 案 EQUAL 归属于当前代码状态（含 rr-v5r94 已提交修复）+ 原件加载恢复，**非本修复引入**。
4. v94 时代分片产品（`semantic_products/v5r94_shard*/`，mtime 08:16 早于 62c1e98c 提交 08:29）抽样与本轮产品**不一致**（如 JS-TRY-002：v94 产品缺 `_CM` 类且 `with json as j` 运行时 TypeError；HEAD 与 HEAD~1 分析器复算均无法复现该产物）→ **v94 分片目录产品系上一轮会话中间工作树状态的陈旧产物，不反映已提交 v5r94 行为**；因 original 加载 ERROR 该差异当时未进入判定（EQUAL 1132=1132 的结论在其测量口径下仍成立：EQUAL→非EQUAL=0）。

### 环境卫生（本轮登记 + 已处置）

- `tools/completeness/semantic_runner.py` 的 `decompile()` 子进程**未带 `-B`**（judge worker 带 `-B`），`core/**` 的 `__pycache__` 可被写入/读取；陈旧缓存（源 mtime/size 恰与缓存头匹配时）可让反编译子进程静默执行旧字节码——与 v94 时代产品不可复现的现象一致（最强解释）。本轮已清理仓库内全部 57 个 `__pycache__` 目录，清理后复算：JS-TRY-002 产品逐字节一致、3 次重复反编译确定性保持。后续轮建议：runner decompile 命令补 `-B` 或每轮闸门前清缓存。

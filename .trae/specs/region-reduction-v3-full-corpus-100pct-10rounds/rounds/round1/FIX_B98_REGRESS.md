# FIX_B98_REGRESS — B98 落地后三处附带回退的封闭（round 1 / 单族窄口径）

分支 `rr-v3r01-f557fd`。本文只处理 B98（commit `3adda063`）在 `core/cfg/region_ast_generator.py`
落地时带来的 3 个语料文件回退，不动 B99/B100/B101，不动 `region_analyzer.py`（第二批 B100 的
未提交改动保持原样），不重构、不扩域。

落地面：`core/cfg/region_ast_generator.py` 单文件，守卫标记 **`[r1-b98-elsescope]`**。
B98 本体（`_is_return_none_join_block` 及其两个消费点）**逐字未动**，见 §6 的反向证据。

---

## 1. 第一分歧实测（修复前产物 vs 原始 pyc，逐指令）

工具：删除产物 → `python -X utf8 pycdc.py -o <base>OK.py <pyc>` → `python -X utf8 test_repros/round1/_diag.py diff <pyc> <OK.py> <unit>`
（`_diag.norm` 已剔除 CACHE，纯位移伪差只在同一 opcode 的 argval 上比较，下表全部是 argval 失配 = 真分歧）。

| 文件 | 单元 | 基线 | 修复前 | 第一分歧（线性索引 / 原始偏移 / opcode） | 原始 argval → 修复前产物 argval |
|---|---|---|---|---|---|
| `site-packages/IQEngine/plugins/plugin_system_accounts/__init__.pyc` | `<module>.AccountPlugin.setup` | 6/6 | **5/6** | idx 234 / off 2010 / `POP_JUMP_FORWARD_IF_FALSE` | `2208` → `2212` |
| `…/account_model/benchmark_account.pyc` | `<module>.BenchmarkAccount._process_mergered` | 20/20 | **19/20** | idx 19 / off 142 / `POP_JUMP_FORWARD_IF_FALSE` | `408` → `412`（同单元 idx 26 `FOR_ITER` 由 `412` → `408`，两枚出口靶互换） |
| `…/account_model/stock_account.pyc` | `<module>.StockAccount._process_mergered` | 25/25 | **24/25** | idx 22 / off 168 / `POP_JUMP_FORWARD_IF_FALSE` | `434` → `438` |

三条分歧的算术形式完全一致：靶点 **+4 字节 = 恰好多出一块 `LOAD_CONST None; RETURN_VALUE`**。

## 2. 一个形状同时解释三处（偏移实测支持）

原始 pyc 的尾部（以 benchmark_account 为例）：

```
143     140 LOAD_FAST  mergered_data
        142 POP_JUMP_FORWARD_IF_FALSE 408     <- if 假边落在「循环体尾」的物理下一块
        ... FOR_ITER 412 ...                  <- 迭代耗尽靶在更后一块
        406 JUMP_BACKWARD 184
143 >>  408 LOAD_CONST None ; RETURN_VALUE
144 >>  412 LOAD_CONST None ; RETURN_VALUE
```

对照实验（本机 3.11.7，`compile()` 直出）证明这两枚靶点是**隐式尾声按路径内联**的指纹：

| 源形状 | `POP_JUMP_IF_FALSE` 靶 | `FOR_ITER` 靶 |
|---|---|---|
| `if m:` / `for …:` 体末无 `return` | 74（先） | 78（后） ← **与原始 pyc 同序** |
| `if m:` / `for …:` / `return None`（臂内） | 78（后） | 74（先） ← **与修复前产物同序** |
| 同上再加函数级 `return None` | 78 | 74 |

⇒ 三处的源码都是同一形状：**`if <cond>:` 的 then 臂以「无 break 的 for 循环」收尾，且该臂是函数/某区域的末段**；
臂尾的 `LOAD_CONST None; RETURN_VALUE` 是 CPython 就地内联的**隐式尾声**，源码里没有 `return None`。
修复前的产物在臂尾多发射了一条 `return None`（`benchmark_accountOK.py` 第 90 行、`__init__OK.py` setup 末行、
stock 同位），于是 if 假边被推到内联尾声之后，产生 +4 靶移。`setup`（三个并列 `if …: for …`）与
两个 `_process_mergered` 属同一族：**同一个机制，偏移实测成立**（不是文件名/函数名巧合）。

## 3. 机制：B98 新增守卫的过度认领

monkeypatch 记录三个文件里 B98 两条新判据的全部命中（`/D/Temp/diag_b98.py`）：

```
benchmark:  HIT ('sink', 340|412|834, '_loop_generate_for:6229')      # join 命中 0
stock:      HIT ('sink', 146|242|340|438|460|938, '_loop_generate_for:6229')  # join 命中 0
__init__:   HIT ('sink', 2212, '_loop_generate_for:6229')             # join 命中 0
```

即三处回退全部由 `_is_region_internal_exit_sink` 在 **`_loop_generate_for` 的 for-else 剥离点**
（HEAD 行号 6229）命中引起；`_is_return_none_join_block` 与 if/elif 臂剥离点（15777）零命中。

认领链实测（最小合成标本 `s1 = if x: for k in items: store.pop(k)`，`/D/Temp/diag_chain.py`）：

```
SINK off=62 instrs=[('LOAD_CONST', None), ('RETURN_VALUE', None)]
   own_region=LoopRegion blocks=[6, 10, 12, 62]
   preds=[10] succs=[]
   anc=LoopRegion  is_querying_loop=True  claims=['else_blocks']  has_break=False
   anc=IfRegion    is_querying_loop=False claims=[]
```

**根因（2 句）**：`_is_region_internal_exit_sink` 的祖先走查从「本块自身的归属区域」起算，
而该 sink 本身就是 `LoopRegion` 的成员块，唯一认领者是**正在裁决这条 else 子句的那个循环区域的
`else_blocks` 字段**；区域归约把「无 break 循环的自然出口」记进它自己的 `else_blocks` 是 fall-through
的记账副产品，任何此类 sink 都满足 ⇒ 判据在循环 else 剥离点**自指恒真**，于是每条
`if …: for …`（无 break、臂尾即函数尾）的臂尾都被追加一条并不存在的 `return None`。
该写法同时与函数自身 docstring ③（「自该区域的 **parent** 起向上」）不一致——偏离发生在代码侧。

## 4. 封闭的守卫条件（落地的判据）

判据仍是**纯区域成员关系**，只补上缺失的作用域条件：认领必须来自「裁决者之外」的区域。

- `_is_region_internal_exit_sink(self, block, deciding_region=None)`：走查命中
  `_anc is deciding_region` 时跳过该层、继续向上（严格附加，默认 `None` 时逐字保持原行为）。
- `_loop_generate_for` 的 for-else 剥离点把本区域传入：
  `self._is_region_internal_exit_sink(_filtered_else_blocks[0] if _filtered_else_blocks else None, deciding_region=region)`。
- if/elif 臂剥离点（15777）**未改**：其裁决者是 `IfRegion`，认领者是臂内 `LoopRegion`（异体），
  仍判 True ⇒ B99 那一支的判据面一字未动（`r1_73` 仍为唯一 B99 失败，读数不变）。

依据条款：§1.2 原则2（每块唯一归属：认领者与被裁决者不同一）、§1.5 C1（局部消费：只消费调用点
已有的区域对象与本块成员关系）、C3（守卫封闭：作用域条件写在守卫内部而非调用点旁路）。
零文件名/函数名/偏移阈值/深度阈值/计数上限——`deciding_region` 是区域身份，不是形态白名单。

消费端白名单不变：判据只读 `block_to_region` 成员关系 + 各区域结构角色字段
（`else_blocks` / `try_blocks` / `handler_entry_blocks` / `finally_blocks` / `orelse_blocks` /
`cleanup_blocks` / `finally_copy_blocks`）、块末 opcode、前驱/后继集合与异常边。

## 5. 前后读数（硬门禁全序）

产物一律「删除 → `pycdc.py -o` 重生成」，未手改任何 `*OK.py`。

| 命令对象 | 修复前 | 修复后 | 门禁 |
|---|---|---|---|
| `plugin_system_accounts/__init__.pyc` | 5/6 failure | **6/6 success** | 6/6 ✅ |
| `…/account_model/benchmark_account.pyc` | 19/20 failure | **20/20 success** | 20/20 ✅ |
| `…/account_model/stock_account.pyc` | 24/25 failure | **25/25 success** | 25/25 ✅ |
| `site-packages/IQCommon/util/cgroup_utils.pyc` | 8/8 success | **8/8 success** | 保持 ✅ |
| `r1_probe_index.json` 电池 | 108/110 units, 44 success / 2 failure | **108/110, 44 / 2**（逐位不变） | 保持 ✅ |
| ├ 允许失败 1 | `_search/handler_ifelse.pyc` 4/5（B101，域外） | 同 | ✅ |
| └ 允许失败 2 | `r1_73_cand_fortry_sinkpair.pyc` 1/2（B99，非本次） | 同 | ✅ |
| `r1_regress_index.json`（本轮新装电池） | 7 标本中 4 MISMATCH（§7） | **14/14 units, 7 success / 0 failure** | ✅ |
| 六套件 pytest | 277 passed / 2 failed / 2 xpassed (3.03s) | **277 / 2 / 2 (3.03s)**，失败名单仍为 `test_B01_simple_if_then_else_merge`、`test_BOUNDARY_02_large_function` | ✅ |
| `import core.cfg.region_analyzer, region_ast_generator, code_generator` | OK | **OK** | ✅ |
| `python -X utf8 -m compileall -q core` | rc=0 | **rc=0** | ✅ |
| 文件完整性 | 单头 BOM、全 CRLF | **BOM 计数 1、lone LF 0、CRLF 全量** | ✅ |

## 6. B98 的战果没有被借道（反向证据）

把 `_is_return_none_join_block` 打桩为恒 False（其余不动），重生成产物后判读：

```
IQCommon/util/cgroup_utils.pyc            8/8 → 7/8 failure
r1_53_cand_trystmt_hret_trailing.pyc      2/2 → 1/2 failure
```

⇒ B98 的收益全部住在 join 判据里；本修复只改 `sink` 判据的作用域，两者无耦合。
`cgroup_utils.pyc 8/8`、`r1_43/r1_44/r1_53/r1_47/r1_48/r1_49/r1_50/r1_52/r1_65` 等 B98 战果标本
在电池里读数逐位不变（108/110，2 失败名单同）。

## 7. 永久回归臂（regression arm）

索引：`test_repros/round1/r1_regress_index.json`（7 条，格式与 `r1_probe_index.json` 一致，LF、无 BOM）。
`r1_probe_index.json` 与任何 `REVIEW.md` **未改动**。

| 标本 | 形状 | 保护对象 | 修复前 | 修复后 |
|---|---|---|---|---|
| `r1_90_regress_if_for_tail_bench` | `if data:` + `for k,v in data.items():` 收尾（benchmark `_process_mergered` 形） | 回退哨兵 | MISMATCH | **MATCH** |
| `r1_91_regress_if_for_tail_stock` | `if data:` + `for …:` 体内含 if（stock `_process_mergered` 形） | 回退哨兵 | MISMATCH | **MATCH** |
| `r1_92_regress_if_for_seq_setup` | 两个并列 `if …: for …:`（`AccountPlugin.setup` 形） | 回退哨兵 | MISMATCH | **MATCH** |
| `r1_93_regress_b98win_try_hret_trailing` | try + handler 终止 return + 函数尾 `return None`（= r1_53/B98 锚点形） | B98 战果 | MATCH | **MATCH** |
| `r1_94_regress_b98win_try_ifelse_hret` | try + 臂内 if/else + handler 终止 return + 尾 `return None`（= r1_43 形） | B98 战果 | MATCH | **MATCH** |
| `r1_95_regress_if_for_tail_in_try` | try 体内 `if …: for …:` 收尾 + handler return + 尾 return | 两族交叉 | MISMATCH | **MATCH** |
| `r1_96_regress_if_for_tail_while_host` | while 宿主内 `if …: for …:` + 函数末同形 | 两族交叉 | MISMATCH | **MATCH** |

4 条回退哨兵在修复前 MISMATCH、修复后 MATCH，3 条 B98/交叉标本修复前后均 MATCH ⇒ 该臂对
「守卫再次自指过度认领」有判别力，对 B98 战果是负对照。

复算命令：

```
python -X utf8 scripts/pyc_verify.py batch --index test_repros/round1/r1_regress_index.json --json D:/Temp/r1_regress.json
```

## 8. 自检（IV.2）与结论

- 新增/改动的方法无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀
  （文件内仅有的两处 `_merge_block_is_*` 命中为既有方法，非本次改动）；无调试残留新增；
  无硬编码深度/计数/偏移上限；无按文件名/函数名的门控。
- 改动仅在 `core/cfg/region_ast_generator.py`，相对修复前工作树净 **+20 行（22 增 / 2 行原地改写）**：
  走查判据 +11 行（8 行注释 + 3 行代码）、docstring 作用域条件 +6 行、调用点注释 +3 行；
  改写的 2 行为守卫签名（+`deciding_region=None`）与 for-else 调用行（+`deciding_region=region`）。
- **无需回退 `3adda063`**：B98 的净收益保持（1 文件 + 电池 108/110），三处附带回退已封闭，
  语料侧净值为正（369/402 基线的三文件回到 success）。

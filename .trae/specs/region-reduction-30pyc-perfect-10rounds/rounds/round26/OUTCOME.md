# Round 26 落地记录：R26-A（出环臂块自带前导语句时不得只发裸 `Break`）

落地提交前基线：`7fbea8cb`（Round 25 R25-A 之后）。
被改文件：`core/cfg/region_ast_generator.py`（唯一），git blob
`9e0f939d9859b3aeda4daec96c06e2c93f734830` → `c10972d0586acf7339eaf32daff41cf43465dae0`
（+13 行 / −1 行；工作树 48312 行纯 CRLF / 0 行裸 LF / UTF-8 BOM 保留）。
`core/cfg/region_analyzer.py` 本轮未动（`64dbaa11e5e2dc436cb8f57c1e0b27da0c4c32dc`，工作树与 HEAD 同哈希）。

## 一、缺陷与根因（取证详述见 `lineB-bulk-loss.md`、`arm-design.md`）

语料靶子：`IQEngine/plugins/plugin_fly_data/__init__.pyc` 的
`ApiMethodPlugin._on_before_trading_start_trading_thread`，严格尺 `orig=66 decomp=62`（缺 4 条），
官方尺因 R97 `_trim_spurious_intermediate_returns` 掩盖而读成 `62/62` 等长（jump 2 / true 19）。

原始字节码（`logs/dump_thread.txt` o38..o48）证明真实源码是

```python
if now >= order.order_time:
    order.commit()      # L239：LOAD_FAST order / LOAD_METHOD commit / CALL 0 / POP_TOP
    break               # L240：JUMP_FORWARD ->404（环尾汇合）
time.sleep(min(order_time - now, ...))   # L242：假分支直落
```

即该 `if` 的**真分支（出环臂）块本身带 4 条前导语句**，跳转只是它的尾指令。
产物里这 4 条整体消失，臂退化成裸 `break`。

阻断点在 `core/cfg/region_ast_generator.py:10084`（函数 `_loop_build_if_with_exit_branches`）。
改之前该处对「出环臂」的分派是**不对称**的：

* `_then_succ in _block_succ_return` 一侧已经按 `get_block_role()` 再判一次，因此 RETURN 形
  能带出自己的前导语句；
* `_then_succ in _block_succ_break` 一侧直接把整块替换成 `{'type': 'Break'}`，
  块内非跳转语句无人发射。

定位方法是**仪器化而非阅读**：`D:/Temp/r26self/probe_break26.py` 在 18 个裸 `Break` 发射点
（同文件 L8965 等）全部打行号戳，只有两处对靶子函数触发——
`R26BRK line=8965 fn=_loop_extract_self_loop_stmts blocks=[16,160,254,258]` 与
`R26BRK line=10084 fn=_loop_build_if_with_exit_branches blocks=[286, 328]`（`D:/Temp/r26self/probe_break_out.txt`）。

## 二、判据 R26-A（同层 · 与既有两处已落地形状同构）

位置：`core/cfg/region_ast_generator.py:10084` 起（替换原先的裸 `Break` 赋值）。

出环臂块的**角色**即区域归约算法原则 1（块内部次序：块 = 前导语句序列 + 尾跳转）在本层的取证：
`get_block_role(_then_succ) == BlockRole.PURE_BREAK` 当且仅当该块除了跳转之外不携带自己的语句，
此时裸 `Break` 与原字节码同形；否则该块是「前导语句 + 跳出」的复合块，必须
先发射 `_generate_block_statements(_then_succ)` 里的用户语句（剔除结构自身的 `Break`/`Continue`），
再接 `Break`，并把该块登记为已生成（`generated_blocks` / `generated_offsets`）以满足原则 2（每块唯一归属）。

同层性依据：判据只读该块的角色与该块内部语句，不读偏移量次序、不读函数名、不读源码形状；
且它与本文件已落地的两个同形件严格同构——同函数下方的 `_block_succ_return` role 分派，
以及 L8965-8974 `_loop_extract_self_loop_stmts` 的 `_jt_user_stmts + [Break]`。
本轮是**把既有的 role 判据补到 break 侧**，不引入新机制。

爆炸半径控制：同函数下方 L10096 的第二处裸 `Break` 分支（无 `_block_succ_break` 命中的兜底臂）
**故意未改**——它没有块可归属，改它就没有实测证据支撑。

## 三、门禁（严格串行；原始日志与记录文件同目录 `logs/`）

镜像法：`D:/Temp/r26land26/r26a.py build` 造 `mirr_head`（原样）与 `mirr_cand`
（断言锚点唯一后逐字节替换，CRLF 与 BOM 原样回写）；`run --arm=…` 的候选只在镜像里，落地前
先断言工作树 `core/` ≡ `mirr_head`，落地后再断言工作树文件哈希 ≡ `mirr_cand` 的同一文件
（实测 `c10972d0586acf7339eaf32daff41cf43465dae0` 两侧相同）⇒ 电池测的字节即 A/B 测的字节即落地的字节。

| # | 门禁 | 结果 |
|---|---|---|
| G0 | 非空判据（合成最小复现，语料无关） | `test_repros/round26_break_prefix/r26a_01_break_prefix_in_while.pyc` 对**落地前字节**（`mirr_head` 镜像）读 `3/4`，缺陷函数 `drain orig=35 decomp=31`（与语料靶子同一 −4 签名），产物 sha `dc299cb3f669e084`（`logs/g0_head.jsonl`）⇒ 判据修的确实是这个形状 |
| G1/G2 | FIX 翻转 + CONTROL 不变 | 同一复现对**落地字节**读 `4/4`、`mism=[]`（产物 sha `1e563e2eb45da044`，`logs/g0_landed.jsonl`）⇒ 该文件另 3 个函数（含 CONTROL）在两臂下均保持匹配；另一份同形孪生复现 `r26a_b2.pyc` head `3/4`（sha `3c8ae4f12cfaea32`）→ cand 与 landed 均 `4/4`（sha 同为 `4a8af9aaacd6e0bd`，`logs/wr.jsonl`、`logs/wr2.jsonl`）；该复现已并入锚点电池（93 例）并对落地字节取基线：93 条记录 `error=0`、空读数 0，其中 28 例带既存残余缺陷者作逐字节比对基线用（`logs/base_landed93.jsonl`（名单 `logs/anchors93.txt`），Round 27 起为 G3 电池） |
| G3 | 前轮（R25 + R24 + 更早）锚点电池 92 例对**落地字节**复跑 | `logs/b92_landed_0.txt`、`logs/b92_landed_1.txt` + `logs/b92_landed.txt`：92 行、`error=0`、`total_functions=0` 的空读数 0；head/cand/landed 三臂 92 条记录逐条相同（差异 0 条）⇒ 承重锚点全部不动 |
| G3′ | 同一电池 head vs cand | `logs/batt92_head_vs_cand.txt`：`SAME=92 IMPROVED=0 BROKEN=0 MOVED=0 ERR=0` |
| G4 | 全 402 文件 A/B（head vs cand，同一 runner、独立产物目录，发货判据） | `logs/ab402_head_vs_cand.txt`：`SAME=400 IMPROVED=1 REGRESSION=0 MOVED=1 ERR=0` ⇒ 没有 ok→fail，爆炸半径 = **2/402 产物** |
| G5 | `single` 靶子 | `IQEngine/plugins/plugin_fly_data/__init__.pyc` → `decompile_status: ok / 20 / 20 / 100.00%`（本轮唯一翻转文件）；`fly/data/quotation.pyc` → `ok 143/143 100.00%`（自 R25 起的承重锚点，未跌） |
| G6 | `batch --index pyc_index.json --all --round 26` 全量复验 | `logs/batch_all26.txt`；索引动 405 行、逐条计数为 `last_tested_round` 402 条 25→26，
加上翻转条目的 `decompile_status`/`matched_functions`/`bytecode_match_rate` 各 1 条
（`git diff -U0 -- pyc_index.json | grep -E '^\+' | sed 's/[0-9]//g' | sort | uniq -c`）。其余字段零改动；文件仍纯 CRLF（4553 行 / 0 裸 LF / 无 BOM） |
| G7 | `stats --index pyc_index.json`（唯一发布序列） | `logs/stats26.txt`：本轮后 `total_functions 5746`、`matched_functions 5639`、`cumulative_match_rate 98.14%`、`ok_pyc 367`、`partial_pyc 35`、`failed_pyc 0`；上一轮收口（`rounds/round25/logs/stats25.txt`）为 `5746 / 5638 / 98.12% / ok 366` ⇒ 只增不减成立 |

`logs/insp_canresume.txt` 是 B1 靶子的区域树实证（见 §五），本轮未在其上落任何判据。

## 四、2 个产物变化的逐项交代

* `IQEngine/plugins/plugin_fly_data/__init__OK.py` `_on_before_trading_start_trading_thread`：
  出环臂补回 `order.commit()`，`break` 退回其后 ⇒ 该函数严格尺 `62 → 66`（与原始等长等序），
  文件 `19/20 → 20/20`，官方 verdict `partial → ok`。
* `IQEngine/plugins/plugin_system_event_source/default_event_sourceOK.py` `events`：
  同一判据命中另一处出环臂（该函数另有两个独立缺陷未修），严格尺读数
  `[orig 510, decomp 486] → [510, 491]`（缺口 `−24 → −19`），函数仍 mismatch、文件 verdict 不变
  ⇒ 记为**改善但非翻转**（A/B 里即 `MOVED gained=[] lost=[]`）。

## 五、本轮否证与移交

* **否证**：B1 靶子 `can_resume_strategy`（−32）曾假设由
  `region_ast_generator.py:11145-11147`「入口块是他链 `elif_conditions` ⇒ 发 `[]`」守卫造成。
  仪器化后该处**从未触发**（无 `R26PROTECT` 戳、产物逐字节不变）⇒ 该假设作废，
  `lineB-bulk-loss.md` 已改写并明确**禁止**在 L11145-11147 落 B1 判据。
  B1 的真实形状（`logs/insp_canresume.txt`）：`IfRegion entry=B0` 的
  `elif_final_else=[B374,B420,B424,B544,B548]` 与其子链 `entry=B178` 的
  `else_blocks=[B198,B244,B374,B420,B424,B544,B548]` 同时认领 B178..B548，
  违反原则 2（每块唯一归属）；发射点尚未定位，仍是任务 #41 / #51 的 B1 线。
* B3（异常尾声 `POP_EXCEPT … LOAD_CONST None RETURN_VALUE` 按退出路径内联复制）与任务 #39
  异常布局族合流，未收口。
* 残余靶：`default_event_source.events` 仍 `−19`（jump 2 / true 157）、
  `fly/data/quotation` 之外的 `DefaultMatcher.match`（259 条指令整体错位，
  `D:/Temp/r26self/dl_DefaultMatcher.match.txt`）。
* 金丝雀：`quotation.pyc` 自 R25 起是承重锚点（必须保持 `143/143`），不再是零副作用样本；
  Round 27 需另选一个未被任何判据命中的语料外 pyc 作零副作用金丝雀。
* 并行的诊断代理（任务 #50）交出的 `D:/Temp/r26diag/` 复现与本节 B1 区域树同源，
  其 `r26_a_break_prefix_nested` 候选与 R26-A 收敛到同一族；Round 27 任何新判据须先对
  **落地字节**复跑其复现，再谈落点。

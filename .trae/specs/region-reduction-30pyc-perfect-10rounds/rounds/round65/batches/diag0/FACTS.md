# R65 · diag0 · FACTS — 清除生成器里的 13 处 `import os as _os_dbg*`

候选臂 = `s1`（`mirr_s1`，spec `specs/cand_r65b0_stripdbg.json`）；对照臂 = `landed`（工作树 `F:/Downloads/pythoncdc-main`）。
本轮**只诊断、只写候选 spec，未落地**；仓库 `core/` 全程未改（见 §10 证据）。

## 0. 结论

| 判据 | 要求 | 实测 | 判定 |
|---|---|---|---|
| 402 支产物 | SAME=402 / REGRESSION=0 / **MOVED=0** | `SAME=402 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0` | PASS |
| 电池 19 项 | 全同 | `SAME=19 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0` | PASS |
| 金丝雀 4 支 | 全同 | `SAME=4 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0` | PASS |
| `py_compile` | OK | `PY_COMPILE_OK`（候选 3 MB 源码 compile 0.7 s） | PASS |
| 产物逐字节 | 0 差异 | 402/402 对产物文件 sha256+size 全等；`build_landed` vs `build_s1` 421 个文件 0 差异（3 725 224 B） | PASS |
| 不可清理项 | — | **无。13 处全部可清理** | — |

候选 `region_ast_generator.py`：`3 103 668 B / c9099bb0fc35` → `3 097 510 B / de510d95b12f`，**−78 行**，BOM 保留、CRLF 50 071、裸 LF **0**、`_os_dbg` 计数 **0**（原 26 处引用全清）、`_sys_dbg` 计数 **0**、`environ.get` 18 → 5。

## 1. 引用普查表（第一步，主风险所在）

词法器 = `re.findall(r'_os_dbg[A-Za-z0-9_]*', line)` 逐行取 token，**不用** `grep -n _os_dbg`（那会把 `_os_dbg_main` 误计入 `_os_dbg`，实测裸名会虚报 12→26 行）。全文件仅 8 个不同名字、共 **26 个引用行**：

| 名字 | import 行 | 引用行合计 | 唯一使用行 | 使用形式 | 环境变量 | 副作用 | 决定 |
|---|---|---|---|---|---|---|---|
| `_os_dbg5` | **L20961** | 2 | L20962 | `environ.get` | `R7_DEBUG_IFGEN`（`== '1'`） | 无 | 删 |
| `_os_dbg4` | **L20999** | 2 | L21000 | `environ.get` | `R7_DEBUG_IFGEN`（`== '1'`） | 无 | 删 |
| `_os_dbg_13` | **L33020** | 2 | L33021 | `environ.get` | `R30_13_DEBUG` | 无 | 删（⚠ 与 R64-D4-B 相邻，§2） |
| `_os_dbg` | **L43773** | 2 | L43774 | `environ.get` | `R23N6_DEBUG2` | 无 | 删 |
| `_os_dbg_main` | **L44507** | 2 | L44508 | `environ.get` | `R23N6_DEBUG5` | 无 | 删 |
| `_os_dbg_lf` | **L47086** | 2 | L47087 | `environ.get` | `R23N6_DEBUG4` | 无 | 删 |
| `_os_dbg_r23n6_trace` | **L47246** | 2 | L47247 | `environ.get` | `R23N6_TRACE` | 无 | 删 |
| `_os_dbg_pre` | **L47294** | 2 | L47295 | `environ.get` | `R23N6_DEBUG3` | 无 | 删 |
| `_os_dbg`（裸名，6 处 import） | **L47331 / 47348 / 47353 / 47358 / 47366** + L43773 | 12 | L43774, 47332, 47349, 47354, 47359, 47367 | `environ.get` | `R23N6_DEBUG` | 无 | 删 |

**关键阴性结果**：BRIEF §1 担心的 `_os_dbg.path.join(...)` / `_os_dbg.open(...)` **在本文件里完全不存在**。
逐 token 核对：每个名字的第二次出现都恰好是紧跟 import 的那一行，形式一律是
`if <name>.environ.get('ENV')`（2 处再带 `== '1'`）。搜索
`.open(` / `path.join` / `.write(` 与 `_os_dbg` 同行的命中数 = **0**。
因此不存在「只删 import 留下用法 → NameError」的实例；本 spec 把 import 与 gated 体**成对删除**，所以即便将来有人打开开关也不会 NameError。

### gated 体内审计（13 处合计 59 行，逐行已核对）
语句种类：`import` 13 / `if` 20 / 局部赋值 13 / `print` 13。
出现过的被调用者只有：`any, get, getattr, isinstance, len, print, sorted, str, type`。
**文件系统调用 = 0**（`open/write/path.join/makedirs/mkdir/rename/remove/flush/shutil` 逐一搜索 = 0 命中）。
13 个 `print` 全部带 `file=_sys_dbg*.stderr` ⇒ 只写 stderr。
赋值的 13 个局部名（`_has_bt2`、`_has_bt2_main`、`_has_bt2_lf`、`_has_bt2_trace`、`_has_bt2_pre`、`_last_op`、`_ch_entries`、`_fcb_dbg`、`_stmt_types`、`_stmt_types_trace`、`_last_stmt`、`_is_expr`、以及各 `_sys_dbg*`）只被同一 gated 体内的 `if`/`print` 消费，**跨出 gated 体零消费者**（已按名字逐个反查全文件）。

### try/except 吞掉？
按缩进回溯每个站点的包围块链：**13 处全部不在任何 `try:` 体里**（`try inside chain: False` × 13）。
所以删除不改变任何异常路径。唯一的「结构后果」是 §2 那 4 个子句整体变空。

## 2. 逐行删除清单

sites 1–9 是「删 import + 其 gated 体」，所在块仍有别的语句，块非空 ⇒ 安全：

| # | 删除行 | 名字/开关 | 保留的邻接锚 |
|---|---|---|---|
| 1 | L20961–20965 | `_os_dbg5` | 上 L20960 `)` ／ 下 L20966 `if _has_boolop_child:` |
| 2 | L20999–21002 | `_os_dbg4` | 上 L20998 `_nested_if_entry_generate[b] = _nr` ／ 下 L21003 `else:` |
| 3 | L33020–33024 | `_os_dbg_13` | 上 L33019 `_pre_store = _mnn[:_si]` ／ 下 L33025 `# Build initial stack:` ⚠ 见 §3 |
| 4 | L43773–43779 | `_os_dbg` / `R23N6_DEBUG2` | 上 L43772 空行 ／ 下 L43780 注释 |
| 5 | L44507–44512 | `_os_dbg_main` / `R23N6_DEBUG5` | 上 L44506 注释 ／ 下 L44513 仅空白行 |
| 6 | L47086–47091 | `_os_dbg_lf` / `R23N6_DEBUG4` | 上 L47085 `if stmt_instrs:` ／ 下 L47092 `return_succ = None` |
| 7 | **L47245**–47253 | `_os_dbg_r23n6_trace` / `R23N6_TRACE` | L47245 `# 追踪 block@456 是否到达此处` 是**只为该探针写的注释**，一并删；L47253 空行一并删以免留双空行 |
| 8 | L47294–47300 | `_os_dbg_pre` / `R23N6_DEBUG3` | L47278–47293 的中文注释块属于 L47301+ 的正式判据，**保留**（已核对：该注释描述 except-handler return 提升，不是探针） |
| 9 | L47331–47334 | `_os_dbg` / `R23N6_DEBUG` | 在 `if _chain:` 体内，同体还有 L47335–47346 正式语句 ⇒ 块非空 |

sites 10–13（原 L47347–47371）是**四个子句的唯一内容就是调试代码** ⇒ 必须连子句头一起删，
否则 `else:` / `elif stmts:` 变空体 = SyntaxError（这正是 `py_compile` 会当场抓住的坑）：

| # | 删除行 | 子句 | 等价性理由 |
|---|---|---|---|
| 10 | L47347–47351 | `else:`（L47330 `if _chain:` 的对侧） | 空体 else ≡ 无 else |
| 11 | L47352–47356 | `else:`（L47315 `if isinstance(...)` 的对侧） | 同上 |
| 12 | L47357–47364 | `elif stmts:`（L47313 的 elif 臂） | 空体 elif ≡ 删该臂；该臂为真时原本什么都不做 |
| 13 | L47365–47371 | `else:`（L47313 链的末端） | 空体 else ≡ 无 else |

L47313 的 `if stmts and _r23n6_in_except_context:` 臂体非空（L47314 起）⇒ 删掉 10–13 后语法与语义都成立。
候选字节实测该处形状（`vfy0` 前置抽查）：`if _chain:` 直接接 `_expr_val = _last_stmt.get('value')`，无残留空子句。

## 3. ⚠ 与 R64-D4-B 相邻（主代理合并时排序用）

**site 3（L33020–33024）落在 R64 刚落地的 `[R64-D4-B]` 规则体内。**
落地字节上 `[R64-D4-B]` 标记行 = **L32990**（`# [R64-D4-B] 识别条件：汇合块首条有效指令是 POP_TOP。此时`），
规则体一直铺到 L33024 之后；本编辑删的是 **L33020–33024**，即 `_pre_store = _mnn[:_si]`（L33019）
与 `# Build initial stack:`（L33025）之间的一段。

* 后果：落地后 L33025 起的所有行**上移 5 行**，R64-D4-B 规则体的尾部行号随之漂移（标记行 L32990 本身在删除点之上，**不漂移**）。
* 因此本 anchor **自带足够上下文**：anchor 文本 = 被删的 5 行原文，其中 L33024 的
  `print(f" value_target={region.value_target} merge={region.merge_block.start_offset} _si={_si} ...`
  是全文件唯一串 ⇒ 在落地字节里恰好出现 **1 次**（已在 §4 实测），不依赖任何行号。
* 合并顺序建议：**本清理 spec 单独排在最前或最后**。它与其它 `region_ast_generator.py` 候选 spec 的 anchor
  在文本上不相交（除 site 3 之外都是远离彼此的独立小 anchor）；若某支 R65 候选也改 R64-D4-B 规则体内部
  （尤其 `_pre_store` / `_init_stack` 附近），需人工确认两侧 anchor 不重叠，否则先落地本清理再叠加。

## 4. anchor 唯一性 + build

`specs/cand_r65b0_stripdbg.json`：13 个 edit，`repl` 一律 `""`，每个 `note` 记 `delete L<a>-<b>` 与归属。
anchor 之间**互不重叠**（按文件顺序排列，相邻的 10–13 各自独立成 anchor，便于与其它 spec 拼接）。

```
 0 occ=1  delete L20961-20965 : _os_dbg5 / R7_DEBUG_IFGEN
 1 occ=1  delete L20999-21002 : _os_dbg4 / R7_DEBUG_IFGEN
 2 occ=1  delete L33020-33024 : _os_dbg_13 / R30_13_DEBUG        <-- ADJACENT TO R64-D4-B
 3 occ=1  delete L43773-43779 : _os_dbg / R23N6_DEBUG2
 4 occ=1  delete L44507-44512 : _os_dbg_main / R23N6_DEBUG5
 5 occ=1  delete L47086-47091 : _os_dbg_lf / R23N6_DEBUG4
 6 occ=1  delete L47245-47253 : _os_dbg_r23n6_trace / R23N6_TRACE
 7 occ=1  delete L47294-47300 : _os_dbg_pre / R23N6_DEBUG3
 8 occ=1  delete L47331-47334 : _os_dbg / R23N6_DEBUG
 9 occ=1  delete L47347-47351 : else:  body debug-only, clause removed
10 occ=1  delete L47352-47356 : else:  body debug-only, clause removed
11 occ=1  delete L47357-47364 : elif stmts: body debug-only, clause removed
12 occ=1  delete L47365-47371 : else:  body debug-only, clause removed
sequential apply OK: 78 lines removed, 2 753 746 -> 2 747 682 chars
```

```
python -X utf8 h62.py build --spec=specs/cand_r65b0_stripdbg.json --dst=s1
mirrors built: head pristine == worktree bytes, cand patched (13 edits, core/cfg/region_ast_generator.py, BOM=True, nl=CRLF)
```
build 内的 `assert io.open(head,'rb').read() == io.open(<worktree core>, 'rb').read()` 通过 ⇒ **落地字节未被改动**。
`assert (_crlf - src.count(CR)) == sum(repl.nl - anchor.nl)` 通过 ⇒ 恰好 −78 行，无夹带。

```
python -X utf8 -m py_compile mirr_s1/core/cfg/region_ast_generator.py  ->  PY_COMPILE_OK
compile(cand_src) 0.7 s        # 3 MB 源码编译很快；R64 说的 >300 s 是 ast.dump 遍历，不是 parse
```

**重复性**：收尾时把 spec 重新 `build --dst=s1` 一次（先 `rm -rf mirr_s1` 由 build 内部完成），
得到 `bytes=3097510 sha=de510d95b12f BOM=True 裸LF=0 _os_dbg=0` —— 与首次构建**逐字节相同**；
三条 TALLY（402 / 电池 / canary）复读仍全 `MOVED=0 ERR=0`。

## 5. 各 TALLY（实测原文）

电池 / 金丝雀（默认 env，落地 vs s1）：
```
=== BATTERY landed-vs-s1 ===
TALLY SAME=19 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0  (unpaired lists=0)
files fully matched: a=14 b=14
=== CANARY landed-vs-s1 ===
TALLY SAME=4  IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0  (unpaired lists=0)
files fully matched: a=4  b=4
```
402 支逐片（`--nshard=4`）：
```
--- shard 0 --- TALLY SAME=101 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0  (unpaired lists=0)
--- shard 1 --- TALLY SAME=101 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0  (unpaired lists=0)
--- shard 2 --- TALLY SAME=100 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0  (unpaired lists=0)
--- shard 3 --- TALLY SAME=100 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0  (unpaired lists=0)
合并（L_all vs S_all，402 条）
TALLY SAME=402 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0  (unpaired lists=0)
files fully matched: a=384 b=384
```
聚合量两臂逐项相同（也是对 R64 落地基线的独立复现）：
```
dump/L_all.jsonl   recs=402 matched=5689/5746 clean=384 err=0
dump/S_all.jsonl   recs=402 matched=5689/5746 clean=384 err=0
dump/battery_landed.jsonl / s1_battery.jsonl   61/68 clean=14 err=0     # 与 R64 G6「电池 61/68、全清 14」逐字相同
dump/canary_landed.jsonl  / s1_canary.jsonl   204/204 clean=4  err=0
sha 多重集两臂相等: True
```

## 6. 逐字节产物证明（比 `ab` 的 16-hex 前缀更强）

`h62.py ab` 只比 `sha256(text)[:16]`。`vfy0.py` 另比**写盘产物文件本身的完整 sha256 + size**：
```
targets in list            : 402
product-file pairs compared: 402
pairs with a side missing  : 0
BYTE-DIFFERENT products    : 0
dump records: landed=402 s1=402 shared=402 (sha|mism)-different=0
```
整目录口径：`build_landed` 421 个文件 vs `build_s1` 421 个，only-in-one=0，**BYTE-DIFFERENT=0**，
比较字节数 **3 725 224 B**。（`__pycache__` 是目录，已从口径外剔除。）

## 7. 开关强制打开的对照（比「env 未设」更强的中性证据）

env 未设时中性只是「没执行」。更强的测试：把 8 个开关**全部设成 1** 再跑两臂。

| 跑法 | 调试 stderr 行数 | 产物 |
|---|---|---|
| `landed` battery + env 全开 | **175** | `SAME=19 MOVED=0 ERR=0`，matched 61/68 clean 14 |
| `s1` battery + env 全开 | **0** | 同上，逐支 sha 与 landed 全开一致 |
| `landed` canary + env 全开 | **616** | `SAME=4 MOVED=0 ERR=0`，matched 204/204 |
| `s1` canary + env 全开 | **0** | 同上 |

⇒ 调试块**确实被执行到了**（616 行来自仅 4 支金丝雀，说明在热路径上高频触发），
但即使全开，两臂产物仍逐支相同、且 0 error / 0 NameError ⇒ 这些块是纯观测性的（只 print 到 stderr）。

各站点的实际 firing 计数（`print` 前缀匹配；`export` 全部 8 个开关 = 1）：

| 站点 | gated print 前缀 | 金丝雀 4 支 | 电池 19 支 |
|---|---|---|---|
| L20961 `_os_dbg5` | `_nested_if check` | 2 | 0 |
| L20999 `_os_dbg4` | `_nested_if_entry_generate` | 208 | 136 |
| L33020 `_os_dbg_13` | `value_target=` | 10 | 2 |
| L43773 `_os_dbg`(2) | `_generate_block_statements block@` | 75 | 3 |
| L44507 `_os_dbg_main` | `reached main stmts` | 75 | 3 |
| L47086 `_os_dbg_lf` | `reached leftover` | 30 | 0 |
| L47246 `_os_dbg_r23n6_trace` | `reached post-stmt` | 49 | 3 |
| L47294 `_os_dbg_pre` | `pre-fix block` | 49 | 3 |
| L47331 `_os_dbg` | `chain=[` | **0** | **0** |
| L47348 `_os_dbg` | `NO chain` | **0** | **0** |
| L47353 `_os_dbg` | `last_stmt is not Expr` | 98 | 21 |
| L47358 `_os_dbg` | `SKIPPED (try_depth=0)` | 18 | 3 |
| L47366 `_os_dbg` | `EMPTY stmts` | **0** | **0** |

⇒ 13 处里 **10 处在本语料上真被走到**（开关开着时），3 处（`chain=[` / `NO chain` / `EMPTY stmts`）
即便开着开关也从未到达 —— 那 3 处是「双重惰性」，删除的安全性更高。
所有 13 处的 print 合计只写 stderr，无任何文件落地。


## 8. ⚠ 工作区 `targets.txt` 是坏的（主代理必读）

交付的 `targets.txt` 402 条**全都带双前缀**，形如
`F:/Downloads/pythoncdc-main/site-packages/F:/Downloads/pythoncdc-main/site-packages/IQCommon/__init__.pyc`
⇒ 按原样 `run` 时 402 条**全部** `RuntimeError('Failed to load …')`。
实测（两臂各跑一遍原样清单再 `ab`）：

```
TALLY SAME=0 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=402  (unpaired lists=0)
files fully matched: a=0 b=0
```

**这个清单不是「假绿」而是响亮地失败**（`h62.py ab` 把带 `error` 的记录先归进 `ERR` 桶，
不参与 `SAME` 统计），所以用它做门禁会直接表现为 ERR=402 而不是全绿 —— 不会误判通过。
按原样存在的路径 **0/402**；剥掉一层前缀后 **402/402 存在且唯一**，
且映射到 **402 个互不相同的 dst 名（0 冲突）** ⇒ §6 的「逐支产物文件对照」是一对一的，没有两支共用一个产物文件。

本工作区已产出 `targets_fixed.txt`（剥掉一层前缀），§5–§6 的所有 402 读数都用它。
`battery.txt` / `canary.txt` 无前缀问题。
**建议主代理集中验证时直接用仓库自己的 `--index pyc_index.json --all`**，
或复用本工作区的 `targets_fixed.txt`；并务必断言 `ERR=0`（只断言 `MOVED=0` 的话，坏清单也能满足）。


## 9. 可复放命令

```bash
cd D:/Temp/opencode/r65gate/diag0
python -X utf8 h62.py build --spec=specs/cand_r65b0_stripdbg.json --dst=s1
python -X utf8 -m py_compile mirr_s1/core/cfg/region_ast_generator.py && echo PY_COMPILE_OK

# 电池 + 金丝雀（默认 env；两臂并行，<300 s）
python -X utf8 h62.py run --arm=landed --list=battery.txt --out=dump/battery_landed.jsonl
python -X utf8 h62.py run --arm=s1     --list=battery.txt --out=dump/s1_battery.jsonl
python -X utf8 h62.py ab --a=dump/battery_landed.jsonl --b=dump/s1_battery.jsonl
python -X utf8 h62.py run --arm=landed --list=canary.txt  --out=dump/canary_landed.jsonl
python -X utf8 h62.py run --arm=s1     --list=canary.txt  --out=dump/s1_canary.jsonl
python -X utf8 h62.py ab --a=dump/canary_landed.jsonl  --b=dump/s1_canary.jsonl

# 402 分片（用修正后的列表；单臂 4 片并行 = 94 s，另一臂 79 s）
for i in 0 1 2 3; do python -X utf8 h62.py run --arm=landed --list=targets_fixed.txt --out=dump/L_$i.jsonl --nshard=4 --shard=$i & done; wait
for i in 0 1 2 3; do python -X utf8 h62.py run --arm=s1     --list=targets_fixed.txt --out=dump/S_$i.jsonl --nshard=4 --shard=$i & done; wait
for i in 0 1 2 3; do python -X utf8 h62.py ab --a=dump/L_$i.jsonl --b=dump/S_$i.jsonl; done
cat dump/L_*.jsonl > dump/L_all.jsonl; cat dump/S_*.jsonl > dump/S_all.jsonl
python -X utf8 h62.py ab --a=dump/L_all.jsonl --b=dump/S_all.jsonl
python -X utf8 vfy0.py          # 逐字节产物对照 + 聚合量

# §7 开关全开对照（诊断用，非门禁）
export R7_DEBUG_IFGEN=1 R30_13_DEBUG=1 R23N6_DEBUG=1 R23N6_DEBUG2=1 R23N6_DEBUG3=1 R23N6_DEBUG4=1 R23N6_DEBUG5=1 R23N6_TRACE=1
python -X utf8 h62.py run --arm=landed --list=battery.txt --out=dump/envL_battery.jsonl 2>logs/envL.err
python -X utf8 h62.py run --arm=s1     --list=battery.txt --out=dump/envS_battery.jsonl 2>logs/envS.err
python -X utf8 h62.py ab --a=dump/envL_battery.jsonl --b=dump/envS_battery.jsonl
```
全程 `python -X utf8`，**未设置 `PYTHONIOENCODING`**；单条命令最长 94 s。

## 10. 未触碰仓库的证据

```
generator  bytes=3103668 sha=c9099bb0fc35   MATCH=True   # 仍等于 BRIEF §0 声明的落地值
analyzer   bytes=1725369 sha=24a88392ee61   MATCH=True
git status --porcelain core/               ->  (空)
```
未运行 `single` / `batch` / `_r13_gate.py` / `land*` / `mbuild` / `mkfinal`；未执行任何 `git` 写操作。
所有产物、镜像、dump 只落在 `D:/Temp/opencode/r65gate/diag0/` 下。

## 11. 不可清理项

**无。** 13 处全部可清理且已实测中性。

## 12. 顺带发现的邻近技术债（**不在本批次范围，未动**）

同一文件另有 5 处同款 `import os as <别名>` 调试导入，BRIEF §0 的 13 处清单不含它们，本 spec 也不含：

| 行 | 别名 | 开关 | 状态 |
|---|---|---|---|
| L696 / L768 | `_os` | `R23N21_DEBUG` | 未动（同款 gated-print 形态，可作 R65 后续批次） |
| L12327 | `_os_ebm` | `EBM_DEBUG` | 未动 |
| L44645 | `_os_w16g` | `R16_DEBUG` | 未动 |
| L44681 | `_os_w16` | `R16_DEBUG` | 未动 |

口径：文件内 `import os as _*` 共 **18** 处 = 本批次 13 + 上述 5；`environ.get` 共 18 处，
本 spec 删 13 处、留 5 处（候选字节实测 `environ.get` 18 → 5，与清单一致，可当 spec 自校验）。

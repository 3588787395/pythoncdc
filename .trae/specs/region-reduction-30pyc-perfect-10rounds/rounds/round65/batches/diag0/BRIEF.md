# Round 65 · diag0 · 技术债批次：清除生成器里的调试导入（只读诊断，禁止落地）

## 0. 任务
`core/cfg/region_ast_generator.py`（落地字节 3 103 668 B / sha c9099bb0fc35 / BOM+CRLF）里残留
**13 处 `import os as _os_dbg*` 调试导入**，实测行号：
```
L20961 _os_dbg5   L20999 _os_dbg4   L33020 _os_dbg_13  L43773 _os_dbg    L44507 _os_dbg_main
L47086 _os_dbg_lf L47246 _os_dbg_r23n6_trace L47294 _os_dbg_pre
L47331 _os_dbg    L47348 _os_dbg    L47353 _os_dbg     L47358 _os_dbg    L47366 _os_dbg
```
（R64 OUTCOME §6.5 的技术债条目；全仓库只有这一个文件残留，`grep -rlc "_os_dbg_" --include=*.py core/` 已证。）
目标是产出一份**可落地的清理 spec**：删掉这些导入，以及**只为它们服务**的临时写盘/打印语句。

## 1. 必须先做的引用普查（这是本批次的主要风险）
只删 `import` 而留着 `_os_dbg.path.join(...)` / `_os_dbg.open(...)` 会让那条代码路径在运行时
`NameError`。所以对每一个不同的名字（`_os_dbg`、`_os_dbg4`、`_os_dbg5`、`_os_dbg_13`、
`_os_dbg_main`、`_os_dbg_lf`、`_os_dbg_pre`、`_os_dbg_r23n6_trace`）都要：
- `grep -n "_os_dbgXXX"` 列出**全部**引用行（不止 import 行），逐条判断是否有写盘/打印副作用；
- 判断该语句是否被 `try/except` 吞掉（若是，删除会**改变异常路径**，必须说明）；
- 给出「删哪些行、留哪些行」的逐行清单。注意 `_os_dbg`（裸名）的 `grep -n _os_dbg` 会连带命中
  `_os_dbg_main` 等，必须用词边界（`grep -nE "_os_dbg\b(?!_)"` 之类）或逐条人工核对。

## 2. 硬约束（违反即作废）
- **禁止修改仓库任何文件**：不许 `git` 写、不许 `single`、不许 `batch`、不许 `_r13_gate.py`、
  不许 `land*`/`mbuild`/`mkfinal`。R64 有一个诊断代理把工作树 core 重排成纯 LF（EVIDENCE §B
  事故），再发生一次本轮就废了。你只能在 `D:/Temp/opencode/r65gate/diag0` 下写。
- 每条命令 **< 300 秒**；402 支一律 `h62.py run --nshard=4 --shard=i` 分片后合并。
- 不许设置 `PYTHONIOENCODING`；一律 `python -X utf8`。
- 清理**不得改变任何产物字节**：这是本批次唯一的正确性判据。

## 3. 门禁（候选臂 vs 落地臂，全部要实测数字）
```bash
cd D:/Temp/opencode/r65gate/diag0
python -X utf8 h62.py build --spec=specs/cand_r65b0_stripdbg.json --dst=s1
# landed 基线：402 支分 4 片
for i in 0 1 2 3; do python -X utf8 h62.py run --arm=landed --list=targets.txt --out=dump/l402_$i.jsonl --nshard=4 --shard=$i & done; wait
for i in 0 1 2 3; do python -X utf8 h62.py run --arm=s1 --list=targets.txt --out=dump/s402_$i.jsonl --nshard=4 --shard=$i & done; wait
python -X utf8 h62.py ab --a=dump/l402_0.jsonl --b=dump/s402_0.jsonl   # 四片都要 TALLY SAME=全部 REGRESSION=0 MOVED=0
python -X utf8 h62.py run --arm=s1 --list=battery.txt --out=dump/s1_battery.jsonl
python -X utf8 h62.py ab --a=dump/battery_landed.jsonl --b=dump/s1_battery.jsonl
python -X utf8 h62.py run --arm=s1 --list=canary.txt  --out=dump/s1_canary.jsonl
python -X utf8 h62.py ab --a=dump/canary_landed.jsonl --b=dump/s1_canary.jsonl
```
**MOVED 必须为 0**：本批次任何产物 sha 变化都是失败信号（说明删掉的语句其实在起作用）。
`SAME=402 / REGRESSION=0 / MOVED=0` + 电池全同 + canary 全同 + `py_compile` OK 才算交付。
（`h62.py ab` 要求两侧行数一致；分片对照时把同一 shard 的 landed/s1 配成一对。）

## 4. 交付
1. `specs/cand_r65b0_stripdbg.json` —— 一条 spec 内含全部 edits（anchor 在落地字节里各恰好 1 次）；
2. `FACTS.md` —— 引用普查表（每个名字：引用行数、是否有副作用、删/留决定）+ 402 分片 TALLY +
   电池/canary TALLY + 可复放命令；
3. `ANALYSIS.md` —— 这些调试导入来自哪几轮（按名字里的 r23n6/r63 等线索）、为何行为中性、
   以及热路径里是否真的发生过文件 I/O（给实测：如在 `--arm=landed` 跑前后计数）。
4. 若发现某处删除**确实**会改变产物，就把它单独列成「不可清理」并给出见证，不要硬删。

## 5. 与本轮 mandate 的关系
本批次**不解决任何 partial**，所以主代理不会用它冒充「至少修好一支」。它的价值是把 3 MB
生成器里的隐藏文件 I/O 与阅读噪声清掉，为后续轮次提速。落地由主代理集中执行。

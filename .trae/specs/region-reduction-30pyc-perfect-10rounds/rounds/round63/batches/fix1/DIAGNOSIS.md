# Round 63 batch 3 — ANALYSIS（随做随追加）

## 基线复核（arm=landed，dump/landed.jsonl）
与 FACTS.md 完全一致，逐字节落地态无需重测：
```
graph.pyc                 29/31  [_get_influence_task 207/195 jd2 td124] [_process_task_queue 378/378 jd1 td118]
fileio_utils.pyc          12/14  [acquire 96/93 jd3 td52] [write 637/637 jd4 td519]
realtime_event_source.pyc 11/12  [clock_worker 1275/1286 jd10 td481]
matcher.pyc               16/17  [match 713/689 jd9 td524]
logger.pyc                28/30  [logging_process 99/95 jd2 td62] [write_logging_thread 113/113 jd1 td40]
```

## matcher.pyc / match —— 缺陷已定位到具体三条语句（探到）
方法：`probe_align.py`（difflib 对齐 orig/decomp 的噪声过滤后指令序列）+
`probe_regions.py`（monkeypatch RegionASTGenerator.generate 转储区域/块归属）+
`probe_consume.py`（包住 ExpressionReconstructor.reconstruct，记录覆盖指定偏移的调用栈）。
产物：logs/match_align.txt、logs/regions_match.txt、logs/consume_match.txt、logs/match_orig_dis.txt。

过滤噪声后 orig=715 / decomp=689，缺口 26 条，与 orig `co_lines` 的逐行指令数精确对上：

| 原源码行 | 语句 | 过滤后指令数 |
|---|---|---|
| 227 | `stock_listed_date = order.asset.listed_date` | 4 |
| 228 | `next_trading_date = self._engine.data_proxy.get_next_trading_date(stock_listed_date, 5)` | 8 |
| 229 | `is_first_five_trading_days = stock_listed_date <= self._engine.trading_dt <= next_trading_date` | 14 |
| 合计 | | **26 = 缺口全部** |

区域归属（logs/regions_match.txt）：
```
 1 BoolOpRegion   blocks=[1696..1818(21) 1820..1828(3) 1830..1832(2)] merge_block=1834..1882(11)
 2 TernaryRegion  blocks=[1696..1818(21) 1820..1828(3) 1830..1832(2)] merge_block=1834..1882(11)
                  condition_block=1696..1818(21)
```
即 CPython 3.11 链式比较 `a <= b <= c`（SWAP2/COPY2/COMPARE_OP/JUMP_IF_FALSE_OR_POP）被建成
「链式比较 IfRegion + 其值语境 BoolOp/Ternary 子区域」，块 1696..1818 是极大直线块，内含
「两条已完结赋值语句 + 链式比较表达式前导」。

生效机制（实测调用栈，logs/consume_match.txt 唯一命中）：
```
_process_if_blocks L21971  child_ast = self._generate_ternary(nested)
_generate_ternary  L34436  cond_expr = self._build_chained_compare_from_region_data(region)
_build_chained_compare_from_region_data L12974 -> _try_build_method_call_chained_compare
_try_build_method_call_chained_compare L13297 left_ast = reconstruct(left_instrs)
    left_instrs = cond_instrs[:left_start] = 偏移 1696..1784 共 14 条  ->  返回 type=Name
```
两条独立缺陷（同源）：
1. `_try_build_method_call_chained_compare` 的左操作数切片取 `cond_instrs[:left_start]`，
   把块内**已完结的前导语句**（227/228，含 `STORE_FAST`）整体当成左操作数吃掉。
   同文件既有判据 ` _extract_ternary_cond_preload` 早就写明「前缀里有 STORE ⇒ 那是
   pre-statement，不是 preload，让位给调用方」；本构造器缺同一条划界。
   结构判据 `_split_block_condition_prefix`（L336，Assert/Loop 两个消费者，纯栈深判据）
   正是为这种「块整体归子区域、块内前导语句归父序列」的划界而存在，此处未接入。
2. `_process_if_blocks` L21978 起：`child_ast = self._generate_ternary(nested)` 返回空时，
   仍然 `for b in nested.blocks: self.generated_blocks.add(b)` —— 子区域一个 AST 都没产出，
   却把它的全部成员块（含 229 的写回 merge 块）宣告为已生成，于是三条语句整体蒸发。
   这违反「每层每个基本块唯一归属」的正半句：唯一归属的前提是**必须有人发射**。

## 证伪 1：候选 spec cand_r63_claim.json —— 在见证上完全 INERT
`specs/cand_r63_claim.json`（把 `_process_if_blocks` L21971 处的
`for b in nested.blocks: generated_blocks.add(b)` / `_generated_regions.add(child_id)`
收进 `if child_ast:` 内部，即「归约产物为空就不登记归属」）：
build c1 成功（BOM/CRLF 保留，1 edit），
```
landed matcher.pyc  16/17  [['match', 713, 689, 9, 524]]
c1     matcher.pyc  16/17  [['match', 713, 689, 9, 524]]
```
逐函数元组**零变化**——与 R62 两支被毙候选同型。已在 c1 臂上再测 sibling 分派
（probe_sib.py，只打印 cond 含 1696 的子区域）：
```
_generate_ternary blocks=['1696..1818','1820..1828'] ctx=store vt=is_first_five_trading_days -> EMPTY
```
`_generate_boolop` 对 BoolOpRegion#1 **从未被调用**。所以「解除登记后交给同层兄弟区域
（BoolOp 抽象节点）发射」这条路根本不成立：BoolOpRegion#1 不在该 else 单元的 nested
分派集合里，块解除登记后也没有第二个主人来发射。→ 判据方向错误，不是生效机制。

## 生效机制（结论）
丢失的 26 条指令 = 值语境链式比较区域 `TernaryRegion(cond_block=1696..1818,
merge_block=1834..1882, merge_context='store', value_target='is_first_five_trading_days',
chained_compare_ops=2)` 在 `_generate_ternary` 里**返回空**，一个 AST 都不产出；
调用方把它记为已生成。即缺陷单点位于 `_generate_ternary` 内部（不在分派层、不在
`_try_build_method_call_chained_compare` 的左切片——那只是同一条错误划界的另一处表现）。

下一步判据（本批未完成，留给 R64）：`_generate_ternary` 对
`merge_context=='store' + value_target + chained_compare_ops>=2` 的区域，CPython 3.11 的
`JUMP_IF_FALSE_OR_POP` 是**链式比较自身的内部短路**，不是三元的分支；正确归约是
`Assign(value_target, Compare(...))`（无三元外壳），并用既有纯栈深判据
`_split_block_condition_prefix(cond_block)`（L336，Assert/Loop 两个既有消费者）把同块
前导语句切出、经 `pre_stmts` 交父序列发射——与 L34401-34407 `_build_ternary_boolop_condition(region, pre_stmts)`
的既有接线完全同构。需要先定位 `_generate_ternary` 内该区域返回空的具体 bail 点
（函数体极长，34425 之后窗口内无 `return None`，逃逸发生在更深处）。

## 证伪 2：最小合成复现未触发缺陷
`test_repros/round63_b3/r63b3_chained_value_ctx_prefix.py`（+.pyc）——
「if/elif 两条含 LOAD_METHOD 的比较 + 两条前导赋值 + 值语境链式比较 + 以其为条件的 if」。
跑法：`python -X utf8 h62.py run --arm=landed --list=targets_repro.txt --out=dump/repro_landed.jsonl --budget=180`
（targets_repro.txt 指向该 .pyc）。实测 **2/2 matched，无缺陷** ⇒ 合成形态缺一个必要成分
（真实函数里该语句位于 if/else 分支内、且分支单元由 `_if_generate_else_branch` 的
`_seq_stmts_c3` 分段送入 `_process_if_blocks`；合成版被当作顺序语句发射了）。
不要把这个 repro 当见证用；见证仍是 matcher.pyc/match（用 targets_match.txt）。

## fly/logger.pyc：独立确认 R62 cand_fixa 判据的入口栈深（任务点名要求）
探针（region_ast_generator.generate 之后转储 BoolOp/Ternary 区域的 merge_block 指令序列）：
```
logging_process #2 BoolOpRegion blocks=[226, 308, 346]
  merge_block 起始指令 = POP_TOP, LOAD_FAST, LOAD_ATTR, LOAD_METHOD, PRECALL, CALL,
                         STORE_FAST, LOAD_FAST, POP_JUMP_BACKWARD_IF_TRUE   (offset 346..)
```
⇒ merge 块**入口栈深 = 1**（or 链幸存的布尔值），且「首个栈顶消费者」就是块首第 0 条
指令 POP_TOP（丢弃该布尔值），其后的 `self.x = ...` 语句与 or 链无关。
R62 第 5 批 cand_fixa 改的是该扫描「遇 POP_TOP 提前停止」——但消费者本来就落在 index 0，
停止条件改与不改，扫描结果同解，所以它在 logging_process 上必然 INERT（实测零变化与此吻合）。
⇒ 该分支判据不是缺陷所在；logging_process 的 -4 条缺失应另找（候选：or 链自身少发射 2 条
   比较指令，需逐指令对齐，本批没时间）。

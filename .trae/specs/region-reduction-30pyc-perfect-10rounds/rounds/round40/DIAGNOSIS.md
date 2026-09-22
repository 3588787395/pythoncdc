# Round 40 诊断 —— 子形状 B：merge_block 不是汇合点（then 臂逃逸回循环头）

落地基线：HEAD `a8225d82`，`core/cfg/region_ast_generator.py` sha256[:20] `cc1254fa30410f2b9954`，
2 988 464 字节 / CRLF 48 474 / UTF-8 BOM 保留（Round 39 落 R39-B 之后）。

目标池（`python -X utf8 D:/Temp/r40gate/pool40.py` 从 Round 39 G6 回填的索引读数）：

```
baseline(landed round39 index, HEAD a8225d82, core sha cc1254fa30410f2b9954):
  files 402 partial 27 sum_deficit 95 deficit1 5 deficit2 11
```

## 一、线索来源与采纳前复核（Round 38 lesson 38.8：点名符号必须先 grep）

本轮不另起诊断线，而是复核 Round 38 线 A 遗留、由 `D:/Temp/r39diagB/ANALYSIS.md` 给出的「子形状 B」
线索。采纳前三项复核全部通过（都在**落地字节**上重做，不在旧字节上沿用）：

1. **发射点仍在原位**：`_if_generate_normal`（`def` 在 16638）内的 merge→else 提升门仍逐字位于
   17099–17117，`if not _mb_meaningful:` 全文唯一（`grep -c` = 1，其余两处 `_mb_meaningful` 是别的局部）。
   R39-B 的 53 行插入点在 ~21561，与本门无重叠。
2. **锚点唯一性**：以 LF 归一文本计，门条件四行块 `if _mb_target is not None …` 出现 1 次，
   `if not _mb_meaningful:` + 两行赋值体出现 1 次 ⇒ 镜像 `build` 断言 anchor count==1 通过。
3. **靶行仍为 partial**：`IQCommon/util/common_func.pyc 17/21`、`IQData/utils/common_func.pyc 22/24`、
   `fly/data/quote.pyc 67/81`、`IQData/plugins/plugin_system_realquote/real_quote.pyc 38/44`
   —— R39-B 没有顺带修掉它们，线索仍然活着。

同时修正旧文档的一处路径错误：`fly/data/real_quote.pyc` **不存在**，`one_prod_to_dataframe` 的实际宿主是
`IQData/plugins/plugin_system_realquote/real_quote.pyc`（本轮按 `pyc_index.json` 逐条核对）。

## 二、根因（归属层，不是发射层）

锚点 `IQCommon/util/common_func.pyc :: fill_kline_data`，严格尺读数 `orig=60 decomp=59`，
缺失指令 `@188 JUMP_BACKWARD -> 138`。CFG（`start_offset [指令区间] succs`）：

```
B@138 [138]          succs=[244,140]   FOR_ITER            循环头
B@140 [140..152]     succs=[154,166]   条件比较 + POP_JUMP_IF_TRUE
B@154 [154..164]     succs=[190,166]   第二析取项 + POP_JUMP_IF_FALSE -> 190
B@166 [166..188]     succs=[138]       真臂体；JUMP_BACKWARD -> 138
B@190 [190..242]     succs=[138]       假臂体；JUMP_BACKWARD -> 138
B@244 [244,246]      succs=[]          RETURN_VALUE
```

分析器交给生成器的区域：

```
IfRegion  blocks=[140,154,166] cond=154 then=[166] else=[] merge=190 exit=190 parent=LoopRegion
LoopRegion hdr=138 back_edge_block=190 back_edge_blocks={190} metadata['natural_back_edge']=190
```

`B@190` 一身二职：IfRegion 拿它当 `merge_block`/`exit`，父 LoopRegion 拿它当 `back_edge_block`。
但它**不是汇合点** —— `B@190` 的前驱只有 `B@154`（假出口），真臂 `B@166` 从不指向它。
于是 `else_blocks=[]` 使 `_if_generate_else_branch`(17117) 返回 None，`orelse` 在 17460 冻结为 None，
`B@190` 改由父循环按自然回边次序发射 ⇒ AST 上 `If(test, body=[…], orelse=None)` 与一条**同级兄弟语句**，
两条臂尾的 `JUMP_BACKWARD` 在重编译时塌缩成一条（少发一条指令）。

已有的 merge→else 提升机制（17099–17116）方向完全正确，只是**判据用错了**：它要求 merge 块「没有有意义的
指令」（纯度），而真实的判据应当是「它根本不汇合两臂」。

## 三、候选判据（同层、纯结构事实）

R40-A（`ANALYSIS.md` §4 原样）：**某条** then 尾块以无条件跳转逃到循环头 ⇒ `merge_block` 归 `else_blocks`。

本轮把它收紧为 R40-A2，理由是可证性而非经验：then 臂若有两条尾块，一条逃逸、另一条落进 merge，
则 merge 仍是真汇合点，「某条尾逃逸」并不足以否定 merge 角色。收紧后的判据（全部为结构事实：块身份 /
后继关系 / 终结符操作码类 / 区域角色；不看名字、不看常量、不看绝对偏移、不看指令计数、不看遍历历史）：

> ①then 臂的任何块都不以 `merge_block` 为后继；且 ②then 臂的**每条**尾块（在 `then_blocks` 内无后继者）
> 的终结边都是无条件跳转且目标恰为包围本 if 的循环头。①+② ⇒ `merge_block` 不是 merge，而是假臂本体。

与既有纯度判据**互斥并联**（`if not _mb_meaningful or _mb_then_escapes:`），纯 merge 分支逐字保留，
不改变其既有世界；`_merge_block_is_then_exclusive`、`[R100 fix]` Continue-兄弟救援段（17483–17516）
均不受该 hunk 触碰。

## 四、门禁实测（严格串行）

| 门禁 | 内容 | 结果 |
| --- | --- | --- |
| G0 | 合成见证（与语料无关，对**落地字节**重跑） | head：`s2_or:seq_-1`、`s7_nested:seq_-1`、`c4_inner_continue:seq_-1` 三处 DEFECT；r40a / r40a2 双臂 `CLEAN 0 bad`。5 条负对照双臂均 CLEAN ⇒ **PASS** |
| G1 | deficit-1（5 文件）+ deficit-2（11 文件）池 | `IQData/utils/common_func.pyc 22/24 → 23/24`（IMPROVED），`REGRESSION=0`；3 行 MOVED 但 `gained=[] lost=[]`（缺陷集合与计数不变）⇒ **PASS** |
| G2′ | `reprobat59` + Round 39 臂尾回边电池（61 条目） | `SAME=60 REGRESSION=0`，唯一 MOVED 行 `r3_04_loop_branch_continue_lost` 双臂均 `3/3` 全匹配；`files fully matched a=50 b=50` ⇒ **PASS** |
| G3 | `anchors107` 承重锚点集 | `SAME=105 REGRESSION=0`，2 行 MOVED（同一文件与其 `_dec` 孪生）双臂均全匹配；`fully matched a=77 b=77` ⇒ **PASS** |
| G4 | 全 402 文件私有镜像双臂 A/B（唯一发货判据） | 见 §五 |

新增电池（本轮已入库，供后续轮次 G2′ 钉住）：
`test_repros/round40_merge_not_a_merge/{r40w_witness.py,r40c_controls.py,pyc/}`；
落地前读数：head `r40w_witness 1/4`（三条见证各差一条 `JUMP_BACKWARD`）、`r40c_controls 10/10`；
候选臂读数：`4/4` + `10/10`。

`r40c_1_two_tails` 是 R40-A2 相对 R40-A 的**判别式对照**（then 臂一逃逸一落 merge）；
`r40c_5_merge_join` 否定「只看假臂单一前驱」的粗糙版；`r40c_3_break` 否定把 `break` 当 `continue`。

## 五、G4 判语与取舍（为什么落 A2 而不是 A）

宽版 R40-A 与收紧版 R40-A2 **都**通过了 G0／G1／G2′／G3，也就是说这四道门禁分辨不出二者；
发货判据只能进一条规则，于是按可证性取舍（两版各自的镜像与 spec 都归档在 `logs/`）：

* `r40c_1_two_tails`（then 臂两条尾块：一条 `continue` 逃逸、一条落进 merge）在宽版下靠
  「两版 AST 指令序列相同」侥幸通过。侥幸不是判据：该形状里 `merge_block` 确有两条入边，是真正的
  汇合点，宽版把它判成假臂本体在语义上就是错的 —— 产物恰好等价只因为 `if c: A; continue` 与
  `if c: A else: B` 同码，一旦 merge 之后还有语句、或该 if 处在 `try` 内，等价就失效。
* 收紧版增加的两项（① then 臂任何块都不以 merge 为后继、② **每条**尾块都逃向循环头）
  恰好就是「merge 不是汇合点」的证明，且 G4 实测收益不降：`IMPROVED=3 / REGRESSION=0`、4 个函数。

⇒ 落 R40-A2（`logs/spec40a2.json`）。宽版 `logs/spec40a.json` 与 `mirr_r40a` 一并留档，
  以便后来者复现这条取舍依据，而不是重新猜一遍。

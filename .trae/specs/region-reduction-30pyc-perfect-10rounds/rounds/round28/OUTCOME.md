# Round 28 — or 短路链的末析取块被 and 链回退二次认领（R28-A）

基线：`de2fd999`（Round 27 落地 ＋ 补记之后）。本轮只落地**一条同层判据**，作用面在
`core/cfg/region_ast_generator.py` 的 `_discover_predicate_and_chain`（生成端 and 短路链
反向回退）。核改动 `+19 / −1`（那 1 行是 docstring 的守卫计数「三条」→「四条」）。

## 一、目标池与两条诊断线（均实测）

索引口径 deficit==1 的文件本轮 11 个（Round 27 落地把它从 12 抬到 11）。两条线：

**线 A —— 异常尾声复制（`save_testds_to_json 314/310`）：方向否证。**
Round 27 代理耗尽轮次未交 `ANALYSIS.md`，其私有目录 `D:/Temp/r28diagA/` 留有三份候选
（`spec_r28a/b/c.json`），判据形状都是**抑制**：本块指令流恰为
`(PUSH_EXC_INFO|POP_EXCEPT)* [+ LOAD_CONST None] + RETURN_VALUE/RETURN_CONST None`
且 `try` 深度 > 0 且本函数同形尾声 ≥ 2 条时不发射 `return None`。三份候选都能把靶子从
`14/15` 抬到 `15/15`、合成复现 `6/7→7/7`，但在 17 文件金丝雀窗与全量上各**回退 12 个文件**
（`files fully matched a=10 b=4`）⇒ 全部否证。真实形状不是「多发了一份隐式 return」，
而是**缺了一份内联副本**：原始 `orig[302:305]` 是
`POP_EXCEPT; POP_EXCEPT; LOAD_CONST None; RETURN_VALUE`，产物侧该位置为 0 条 —— CPython 3.11
按 except 的每条退出路径各内联一份清理尾声，本核只发了一份。故此族需要的是**发射侧**判据，
不是抑制侧。移交 Round 29+（`fly/common/flytools.pyc :: FileLock.acquire` 的 ① 子形同族）。

**线 B —— `fly/common/custom_tools.pyc :: memory_handler` 过量发射 +4：本轮采纳。**
严格尺读数 `65/69`，唯一 hunk 是 `replace orig[44:45] → decomp[44:49]`。产物文本：

```
    if user_id in memory_control_dict.keys():
        if ('GB' in user_memory or 'GiB' in user_memory) and float(...) <= float(...):   ← 同一文件的正确孪生
    elif 'GB' in user_memory or 'GiB' in user_memory:
        if 'GiB' in user_memory and float(...) <= float(...):                             ← 多了首合取支
```

即 elif 臂的 or 链末析取成员（块 254）在臂体内又被当成嵌套 `if` 的首合取支发射了一遍
（`LOAD_FAST / LOAD_CONST / CONTAINS_OP / POP_JUMP_IF_FALSE` 四条）。

根因位置由**打戳探针**确定（不是读码猜）：`D:/Temp/r28self/probe28_spec.json` 在
`_discover_predicate_and_chain` 的前驱候选接受点与链返回点各打一处戳，`region_ast_generator`
镜像跑单文件实测得

```
[R28P1] p=254 cur=262 gen=True pure=True elifcond=[]
        own=[('BoolOpRegion', entry/merge=[246,420], blocks=[254,246]), ('Region', blocks=[254])]
[R28P2] chain=[254, 262] pure=[True, True]
```

`gen=True` 是决定性的：块 254 **已登记在 `self.generated_blocks`**（`_if_generate_elif_chain`
path (c) 在 15361–15362 行把 `elif_boolop.blocks` 全数入账），它的指令流已由外层 elif 的
or 短路链认领。

## 二、判据 R28-A（原则 2 唯一归属 · 该回退的第四条放弃守卫）

```python
if p in self.generated_blocks and self._chain_block_is_pure(p):
    return None
```

同层性：两个合取项都只读**块自身**的属性（登记状态、块内指令纯净性），不读绝对偏移次序、
不读函数名／常量、不读源码形状；作用面限于本回退自己收集的那条链，命中即放弃整条链，
与既有三条放弃守卫同源（只删不增，不命中即交由既有单条件生成路径）。

既有三条守卫为何都不命中（逐条实测）：
1. 「前驱候选是某结构区域的条件块」—— 254 不是任何区域的 `condition_block`；
2. 「前驱候选是任一其它 IfRegion 的 `elif_conditions` 成员」—— 探针 `elifcond=[]`：
   or 链成员登记在 `BoolOpRegion.blocks`，**不在** `elif_conditions`，这条原则 2 守卫的
   认领集合本来只覆盖了 elif 链的第一级；
3. J2「链首是另一纯块前向条件跳转的落点」—— 块 246 的 `POP_JUMP_IF_TRUE` 目标是臂体入口
   262 而非 254，254 是靠 fallthrough 进入臂体的末析取支，落点判据天然看不到。

**纯性合取项不是装饰，是被第二条实测否决出来的**：只用 `p in generated_blocks`（以及只用
「p 是另一区域的 blocks 成员」的窄版）两版候选，在 402 全量上都把
`fly/data/quote.pyc :: load_bars_from_hundsun` 从 470 打到 446（见 §五）。链首按既有设计
**允许自带前导语句**（docstring：「链首（最深前驱）允许前缀语句……提升为 pre_stmts 是
程序序保真的」），这类块即便已登记，其语句本就由本回经受 `pre_stmts` 归属；放弃会连语句
一起丢。带纯性合取项后，探针打戳版在 quote.pyc 上恰好打印一次
`[R28C] suppressed p=144 cur=332 pure=False chain=[332]`，与实测的 470 恢复互相印证。

## 三、门禁（严格串行；原始日志见 `logs/`）

| # | 门禁 | 结果 |
|---|---|---|
| G0 | 非空判据（语料无关合成复现） | `test_repros/round28_or_tail_conjunct/r28a_01_or_tail_as_nested_conjunct.pyc`：head 读 `3/4`，缺陷函数 `case_or_tail_operand_reused orig=33 decomp=37`，与语料靶子**同一签名**（`[name, 65, 69, 1, 21]` ↔ `[name, 33, 37, 1, 21]`）；两条 CONTROL（臂体内真 and 链、or 链＋带 else 的嵌套 if）在 head 已匹配 |
| G1/G2 | FIX 翻转 ＋ CONTROL 不变 | cand `4/4`、`mism=[]`；两条 CONTROL 在两侧均匹配（`logs/rb_head.jsonl`、`logs/rb_cand.jsonl`） |
| G2′ | 前轮合成复现电池（本地现存 38 个 `test_repros/**.pyc`） | `logs/reprobat_tally.txt`：`SAME=37 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`（唯一 IMPROVED 就是本轮新复现）⇒ 判据没有打坏任何前轮复现 |
| G1′ | 语料靶子 | `fly/common/custom_tools.pyc` head `5/6`（`memory_handler 65/69`）→ cand `6/6`、`mism=[]` |
| G3 | 94 条承重锚点电池（上轮落地基线 `base_landed94.jsonl`） | `logs/batt94_landed_vs_candc.txt`：`SAME=94 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`；空读数 0；Σmatched 270 / Σtotal 298。该电池跑在无注释的测量变体上；正式镜像与它在全部 402 个产物上 `sha` 逐条相同（见 G4 行），故锚点读数即落地字节读数 |
| G4 | 全 402 文件 A/B（head vs **落地字节同形镜像** arm=cand，发货判据） | `logs/ab402_head_vs_cand.txt`：`SAME=401 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`；`files fully matched a=368 b=369`；带注释的正式镜像与测量用的无注释变体在 402 个产物上 `sha` **逐条相同**（差异 0 条） |
| G4′ | 对 G4 唯一变化产物跑严格尺 | `logs/strict_g4p.txt`：`STRICT-BETTER`，`memory_handler` head `65/69 seq_len` → cand `65/65` 无缺陷；文件级 strict clean `5/6→6/6`、σ `4→0` |
| G5 | `single` 靶子与承重锚点 | `fly/common/custom_tools.pyc ok 6/6 100.00%`；金丝雀 `fly/data/quotation.pyc` 保持 `ok 143/143`、`plugin_system_persist/__init__.pyc` 保持 `ok 15/15` |
| G6 | `batch --index pyc_index.json --all --round 28` 全量复验 | `logs/batch_all28.txt`：rc=0、`[402/402]` 跑完、无 traceback／timeout。索引改动逐字段核对（`logs/index_delta28.txt`）：`last_tested_round` ×402，`bytecode_match_rate`／`decompile_status`／`matched_functions` 三者只落在**同 1 条**翻转型目（`0.8333…→1.0`、`partial→ok`、`5→6`），键集合无增删、条目数 402、Σ`function_count` 5746 不变；`site-packages` 下变化产物 1 个（`git status --porcelain` 实测 = `fly/common/custom_toolsOK.py`，与 G4 的 `MOVED=0 IMPROVED=1` 一致） |
| G7 | `stats --index pyc_index.json` | `logs/stats28.txt`：`total_pyc 402 / verified_pyc 402 / ok_pyc 369 / partial_pyc 33 / failed_pyc 0 / total_functions 5746 / matched_functions 5641 / cumulative_match_rate 98.17%` |

## 四、唯一产物变化的逐项交代

G4 的 `SAME=401 IMPROVED=1 MOVED=0` 意味着**整个语料只有一份产物字节变了**：
`site-packages/fly/common/custom_toolsOK.py` 第 35 行

```
-        if 'GiB' in user_memory and float(max_memory_size) <= float(user_memory.replace('GB', '').replace('GiB', '')):
+        if float(max_memory_size) <= float(user_memory.replace('GB', '').replace('GiB', '')):
```

官方尺 5/6→6/6（翻转为 ok），严格尺 `seq_len` 缺陷消除、σ 4→0。同文件同函数里那个**正确**
的孪生形状（首臂 `if ('GB' in um or 'GiB' in um) and float(...) <= ...:`）逐字节不变 ——
它的外层 `or` 是真 `and` 的左操作数，链首不受本守卫约束。

## 五、本轮的方法论收获：MOVED 里混着真回退，严格尺逐条核才分得开

G4 的**第一版读数**（无纯性合取项的两版候选）是
`SAME=400 IMPROVED=1 REGRESSION=0 MOVED=1`，官方尺看似干净。唯一那条 `MOVED` 是
`quote.pyc :: load_bars_from_hundsun`：`matched_functions` 不变（该函数两侧都不匹配），
但产物从 `477/470` 变成 `477/446` —— 严格尺 σ 由 7 恶化到 31，多丢 24 条指令，
连函数体里那条日志 f-string 语句一起丢。若只按官方尺发货，这就是 Round 27 已固化的
G4′ 规则要拦的那一类：**凡 MOVED 必须回到严格尺逐函数三元组核一遍**。本轮把它推到下一步：
MOVED 不是「中性重排」的同义词，其中可能是真回退；否决证据（p=144 非纯、自带前导语句）
一旦读出来，判据的同层边界就自动收紧成「已登记 **且** 纯操作数块」。

顺带留下的新线索（两侧都有的缺陷，本轮未动）：`load_bars_from_hundsun 477/470` 那 7 条缺口
正落在 `p=144` 这个「既在 `generated_blocks` 里、又自带前导语句」的双重认领块上 ——
反方向的同一归属问题，见 §六。

## 六、残余与移交

* **异常尾声族（线 A）**：需要**发射侧**判据 —— 按 except 的退出路径补内联副本
  `POP_EXCEPT; POP_EXCEPT; LOAD_CONST None; RETURN_VALUE`；三份抑制型候选的否证数据在
  `D:/Temp/r28diagA/`（`ab_head_w17.jsonl` / `ab_r28b_w17.jsonl` / `strict_w1_head.txt`）。
  靶子 `plugin_system_risk_calculation/function.pyc` 仍 `14/15`、`fly/common/flytools.pyc`
  仍 `64/65`（混形：5 指令 raise 尾声被简化 ＋ 环尾 `JUMP_BACKWARD 42` 丢失）。
* **新线索**：`fly/data/quote.pyc :: load_bars_from_hundsun 477/470`（本轮以反证暴露）。
* 未动残余：`default_event_source.events −19`、`matcher.DefaultMatcher.match −26`、
  `realtime_event_source.clock_worker +16`、`instance._init_config −1`／`datetime +6`、
  `replace_utils.decrypt_database_url +29`、`plugin_fly_data/strategy.pyc` 两条、
  `fly/dumpload/load_daily.pyc` 三条。
* Round 29 电池基线：`anchors94.txt` 继续承重，本轮新增靶子 `custom_tools.pyc` 与前轮
  `plugin_system_persist/__init__.pyc`（必须 15/15）、`fly/data/quotation.pyc`（143/143）。
* 新增合成复现 `test_repros/round28_or_tail_conjunct/`（`.py` 入库，`.pyc` 由
  `python -X utf8 -c "import py_compile;py_compile.compile(...)"` 重生成，`*.pyc` 已 gitignore）。

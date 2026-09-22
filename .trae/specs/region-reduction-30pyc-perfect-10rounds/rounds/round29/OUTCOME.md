# Round 29 — 同一 IfRegion 的两条臂同时认领汇合块（R29-A）

基线：`d90f41e5`（Round 28 落地 ＋ 归档之后）。本轮只落地**一条同层判据**，作用面在
`core/cfg/region_analyzer.py` 的 IF_THEN / IF_THEN_ELSE 区域组装处（生成端之前）。
核改动 `+15 / −0`（其中 11 行是原则 2 的理据注释，判据本体 4 行）。落地后该文件与工作
镜像 `D:/Temp/r29gate/mirr_cand` **sha256 逐字节相同**（`e3fde286828754cd…`），
`git diff --numstat` = `15 0`，原有混合 CRLF/LF 与「本文件无 BOM」两条不变量均保持。

## 一、目标池与三条线（均实测）

索引 `deficit==1` 的文件本轮 9 个（Round 28 落地把它从 11 抬到 9）。其中 2 个是线 A 已定性
未收口的靶子，其余 7 个是线 B/C 的聚类对象。三条线：

**线 A —— 异常尾声发射侧（Round 28 移交项①）：未收口。** 诊断代理在 150 轮上限处终止且
未交 `ANALYSIS.md`，原样移交 Round 30（靶子 `plugin_system_risk_calculation/function.pyc`
`14/15`、`fly/common/flytools.pyc` `64/65`）。

**线 B —— 七个未探明 deficit-1 文件的形状聚类（代理交付 `D:/Temp/r29diagB/ANALYSIS.md`）
与线 C（编排方独立实测）合流。** 七个文件聚成四簇：

| 簇 | 形状 | 成员（orig/decomp） |
|---|---|---|
| A | **汇合块被臂内认领**（两臂共同到达的 join 块被收进某条臂的块列表） | `load_daily 913/913`（等长、单跳转槽）、`events 510/491`、`match 713/689`、`clock_worker 1275/1291` —— 4/7 |
| B | 已生成区域体被二次走查（过量发射） | `decrypt_database_url 295/324`、`clock_worker` 的 D2 份额 |
| C | 链式比较条件块整体未发射（真 deficit，需「增」） | `tick_worker_thread 268/247` |
| D | 函数级共享 `return None` 尾声按分支内联 | `_init_config 86/84`（R16 J1 的**在册反例**） |

锚点取 A 簇里唯一**计数中性**的 `fly/dumpload/load_daily.pyc :: <module>`——同形块换位、
不增不减、且是该文件唯一缺陷，是池中最锋利的见证。

## 二、取证链（全部为镜像打戳实测，两次否证在先）

1. **11 处 `merge = else_succ` 全数打戳**（arm `stamp`）：命中 8 次，落点
   1116/2768/960/796/686/472/472/368，**没有一次涉及 2478** ⇒ 汇点塌缩（R13c/`_25b`）
   与本轮无关。第一版戳因 `%s` 少一个占位符抛 `not all arguments converted` 使整轮 0 输出
   ——**戳不落盘是探针坏了，不是没有命中**，修好后才有上面这组读数。
2. **Round 28 判据的邻位假设否证**（arm `p29c`）：`_cr.then_blocks.append(_sb)`
   （`region_analyzer.py:1847`）那把 append 戳 0 次命中，其循环头戳的 4 次读数
   `sb=370/390/582/288` 无一次为 2478；且该臂产物与落地核逐字节相同（913/913/1/19）
   ⇒ 双重认领不发生在 shared_block 后处理。线 B 的第二把戳独立复现同一 0 命中。
3. **构造点一击命中**（arm `p29d`，三处 `region = IfRegion(` 之前＋生成端消费点之前，
   以 2478 为门）：

```
[R29D1] site=17888 cfg=<module> entry=740 merge=2626
        else=[2456, 2478, 2562]
        then=[…, 2022, 2478, 2086, 2176, 2562]
[R29D2] FINAL 同集合（生成端消费时未再变化）
```

即 **2478 与 2562 同时是该区域的 then 体与 else 体**。`_process_if_blocks` 按
`start_offset` 升序遍历臂块（`region_ast_generator.py:20392`），于是 join 块 @2478 被排在
else 臂完成之前发射 ⇒ then 臂打印了本该在 if/else 之后的语句、else 臂被推到它后面，
官方尺表现为「指令数全同、一个跳转槽错位」。

既有的「IF_THEN merge 候选识别」（`region_analyzer.py:17850-17878`）整段被
`if merge is None and not else_blocks` 挡在门外（本例 `merge=2626`、`else` 非空），
而它自己的注释早已写明「`then_blocks` 包含 merge 块 ⇒ AST 生成错误」。

## 三、判据 R29-A（原则 2「每块唯一归属」的臂间共享块取消认领）

```python
if then_blocks and else_blocks:
    _arm_shared = set(then_blocks) & set(else_blocks)
    if _arm_shared:
        then_blocks = [b for b in then_blocks if b not in _arm_shared]
```

同层性：判据只读**两条臂自己的块列表的交**（块身份与归属状态），不读绝对偏移、不读函数名
／常量、不读指令条数、不读源码形状。理据是控制流事实：then 与 else 是互斥路径，被两臂同时
认领的块只能是两臂共同到达的汇合点，任何一臂把它当体内块都是越界吸收。

只删不增：`all_blocks` 取两臂之并，从 then 臂摘出不丢失任何块，只是取消双重认领；该块
仍在 CFG 中未认领，由父区域的既有顺序走查在整条 if/else 之后发射。判据不命中时逐字节不变
——G4 的 `SAME=401`（402 个文件里只有 1 个变）就是这条断言的全量证据。

## 四、门禁（严格串行；原始日志见 `logs/`）

| # | 门禁 | 结果 |
|---|---|---|
| G0 | 语料无关合成复现 | **未取得，如实记录**：把落地核产物与候选核产物各自编译回 `.pyc` 再回灌（`r29a_03`/`r29a_04`），两把尺均 `23/23 mism=[]`——本族缺陷在「分析器对**原始字节码布局**的双认领」，不存在能复现它的源级合成文件。据结构仿写的合成件在落地前后读数不变（`r29a_01_shape_mimic_and_controls.pyc` 两核均 `2/2`，含三条 CONTROL 全匹配），已入库充当判据的**非触发面**；发货证据改由语料靶子（G1′）＋严格尺（G4′）承担。写 G0 过程中另暴露一条独立缺陷 `r29x_01_module_if_deficit_witness.pyc :: <module> 142/138`（jump=2 / true=122，两核同形失败，R29-A 未触及），随本轮移交 |
| G1′ | 语料靶子翻转 | `fly/dumpload/load_daily.pyc` `22/23 → 23/23`、`mism=[]`（`logs/g4_ab402.txt`、`logs/g5_single.txt`） |
| G2′ | 前轮 38 个合成复现电池（对**落地字节**基线） | `SAME=38 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`（`logs/g2prime_battery38.txt`）⇒ 没有打坏任何前轮复现 |
| G3 | 96 条承重锚点电池 | `SAME=96 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`；空读数 0；两侧 Σmatched 280／Σtotal 308 相同（`logs/g3_battery96.txt`） |
| G4 | 全 402 文件 A/B（落地前基线 vs 候选镜像，发货判据） | `SAME=401 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`；Σmatched `5641 → 5642`（Σtotal 5746 不变）；完全匹配文件 `369 → 370`；唯一 IMPROVED 行 `a_mism=[['<module>', 913, 913, 1, 19]] b_mism=[]` |
| G4′ | 对 G4 唯一变化产物跑严格尺 | `STRICT-SAME`：文件级 clean `22/25` 两侧相同、σ 两侧均 0；函数级 `<module> 913/913` 由 `seq_diff`（整段错位）改为 `target_diff`（局部跳转目标归属）——**发射次序已修复，源级嵌套归属为残余线索** |
| G5 | `single` 靶子与承重锚点 | `load_daily.pyc ok 23`；`fly/data/quotation.pyc` 保持 `ok 143`、`plugin_system_persist/__init__.pyc` 保持 `ok 15`、`fly/common/custom_tools.pyc`（Round 28 靶子）保持 `ok 6`。三份金丝雀产物被 `single` **重新生成后与 HEAD 逐字节相同**（`git status --porcelain` 全库只列 3 个改动：核、索引、`load_dailyOK.py`） |
| G6 | `batch --index pyc_index.json --all --round 29` 全量复验 | `logs/batch_all29.txt`：rc=0、跑完 `[402/402]`、无 traceback。索引改动逐字段核对（`logs/index_delta29.txt`）：402 条目路径列表逐条相同、键集合无增删；除轮次戳 `28→29`（402 条）外**只有 1 条**真实改动，正是翻转目 `fly/dumpload/load_daily.pyc`（`partial→ok`、`matched_functions 22→23`、`bytecode_match_rate →1.0`），与 G4 的 `IMPROVED=1 MOVED=0` 同一条目；Σ`function_count` 5746 不变 |
| G7 | `stats --index pyc_index.json` | `logs/stats29.txt`：`total_pyc 402 / verified_pyc 402 / ok_pyc 370 / partial_pyc 32 / failed_pyc 0 / total_functions 5746 / matched_functions 5642 / cumulative_match_rate 98.19%` |

## 五、唯一产物变化的逐项交代

G4 的 `SAME=401 IMPROVED=1 MOVED=0` 意味着**整个语料只有一份产物字节变了**：
`site-packages/fly/dumpload/load_dailyOK.py` 第 466-472 行，那条 `print('++++++…++++++：%s'
% time.strftime('%Y%m%d %H:%M:%S', time.localtime()))` 从 `then` 臂尾移到 `else` 臂尾：

```
                 bsuccess = True
-                print('++++++…++++++：%s' % …)
             else:
                 print("ERROR:…000300.SS…600570.SS…")
+                print('++++++…++++++：%s' % …)
```

原始字节码里该块（@2478）是两臂的汇合点，正确的源级位置是**整条 if/else 之后**。本轮修掉的是
**发射次序**（该语句不再排在 else 臂完成之前），官方尺据此从 `913/913/1/19` 到 `mism=[]`；
源级**缩进归属**仍未修好——严格尺残余的 `target_diff`（#596）正是这一条，已写进移交项②。
同文件其余 22 个函数、以及那两条臂自身，逐字节不变。

## 六、方法论收获：G0 不可得时，发货证据换成什么形状

这一族的特殊性在于缺陷发生在**分析器读原始字节码布局**的那一刻，而不是发射器写产物那一刻：
把产物（无论修复前后）编译回 `.pyc`，得到的是一个「两臂不共享块」的干净布局，回灌后两核读数
相同——所以 G0 型「源级合成复现」在本族**原理上不可能成立**，不是没找到。可行的替代证据是三
件套：① 语料靶子翻转且是该文件唯一缺陷（G1′）；② 判据触发面在全量上只有 1 个文件（G4
`SAME=401`），使「不命中即逐字节不变」得到全量检验；③ 一条按结构仿写的合成件在两侧同读数，
把它登记为**非触发面锚点**，供后续轮次的电池守住「这条判据不许扩大到那里」。写 G0 的尝试没有
白做：它顺手产出了 `r29x_01` 这条新的语料外缺陷见证（两核同形失败），比原靶子更易守。

## 七、残余与移交

* **R29-A 的剩余半条**：`load_daily :: <module>` 严格尺 `target_diff`——汇合块不再抢次序，
  但产物仍把它显示在 `else:` 臂内而非 if/else 之后。同簇另外三个成员本轮未动，因为它们各自
  还叠加别的形状：`default_event_source :: events 510/491`（循环体前导语句出现在回边位置）、
  `matcher :: DefaultMatcher.match 713/689`（281 指令区域被推迟到函数尾并旋转）、
  `realtime_event_source :: clock_worker 1275/1291`（R22/R23 在册残余 D2＋D3）。
* **线 A（异常尾声发射侧）**：Round 28 已定性为需**发射侧**判据（按 except 退出路径补内联
  副本），本轮代理耗尽轮次未收口，靶子 `function.pyc 14/15`、`flytools.pyc 64/65`。
* **新移交**：合成件 `r29x_01_module_if_deficit_witness.pyc :: <module> 142/138`
  （jump=2 / true=122，两核同形失败）——语料外的模块级 if/def 缺失见证。
* **B/C/D 三簇未动**：`decrypt_database_url 295/324`（二次走查，需放弃发射侧，R28-A 同族）、
  `strategy.pyc :: tick_worker_thread 268/247`（链式比较条件块丢失，真 deficit）、
  `instance.pyc :: _init_config 86/84`（共享 `return None` 尾声内联，R16 J1 在册反例）。
  另有 Round 28 留下的 `quote.pyc :: load_bars_from_hundsun 477/470` 与 f-string 族。
* Round 30 电池基线：`anchors96.txt` 继续承重，承重锚点新增
  `test_repros/round29_arm_shared_join_claim/r29a_01_shape_mimic_and_controls.pyc`（必须 2/2）
  与 `fly/dumpload/load_daily.pyc`（必须 23/23）；`quotation.pyc` 143、
  `plugin_system_persist/__init__.pyc` 15、`custom_tools.pyc` 6 不变。
* 新增合成复现目录 `test_repros/round29_arm_shared_join_claim/`（`.py` 入库，`.pyc` 由
  `python -X utf8 -c "import py_compile; py_compile.compile(...)"` 重生成，`*.pyc` 已 gitignore）。

# Round 34 OUTCOME —— 两条线均被门禁/测量否证：本轮 `core/` 零改动

靶轮：Round 33 G6 回写的索引所对应的落地字节（commit `762e8213`，核
`core/cfg/region_ast_generator.py` sha256[:20] `2d3a5d51d114da77d3d4`）。
设计稿与逐条测量见 `arm-design.md`；本文件只记结论与证据指针。

## 一、结论

1. **未发货**：本轮没有任何同层判据通过门禁，`core/` 一个字节都没写，受跟踪产物一份都没变。
   唯一的候选（线 B 的 R34-E）在 **G2′ 上以两条回退被否证**，因此没有进入 G3／G4，
   也没有落地 ⇒ 不需要 G5／G6／G7。
2. **索引未被破坏**：本轮把全 402 文件在 `head` 臂（落地字节的镜像）上整批复测，
   与 `pyc_index.json` 逐文件比对 **0 冲突**，`Σmatched 5646 / Σtotal 5746` 与索引一致
   （`logs/index_vs_head_arm34.txt`）。这是「索引在本轮字节上仍然是实测值」的证明，
   不是自报数。
3. 两条诊断线（各 150 轮次上限）都由**编排方接手**并交出一手闭合的根因链：
   线 B 的判据被证明**在这一族原理上不可判**（见 §三），线 A 的根因链闭合到具体发射站点、
   附带损伤也被语料级实验量出（见 §四）。二者合起来构成 Round 35 的开工前置。

## 二、目标池与基线（实测，非沿用）

```
baseline(landed round33 index, HEAD 762e8213, core sha 2d3a5d51d114da77d3d4): files 402 partial 30 sum_deficit 100 deficit1 7 deficit2 12
```

* 承重锚点电池 `anchors104.txt`（Round 33 的 102 由 `anchors98` ＋ Round 31/32 合成件重建并与
  `round33/logs/list_anchors102.txt` 逐条全等，再 ＋ `r33a_witness.pyc` ＋ 靶子 `utils.pyc`）。
  落地臂 `logs/a104_landed.jsonl`：104 条、0 error、30 条非全匹配（锚点固有），
  两个新锚分别 `17/17`、`22/22`，与 Round 33 §七 预告一致。
* 上一轮合成复现电池 `reprobat39.txt` ＝ `reprobat38` ＋ `r33a_witness.pyc`；落地臂
  `logs/b39_landed.jsonl`：39 条、0 error、28 条全匹配。
* deficit-1 池 7 个文件逐个 `--arm=landed` 复测（`logs/landed_d1.txt`），deficit-2 池 12 个同尺
  复测（`logs/landed_d2.txt`，0 error）。

## 三、线 B（代理 A2 → 编排方重量）：R34-E 在 G2′ 被否证，并证明这一族不可判

* 交付物 `core/cfg/region_analyzer.py` 的单条豁免（`spurious = [eb for eb in lr.else_blocks …]`
  一行，加「`eb` 的入边集恰为子环头块且入边是头块 `FOR_ITER`/`GET_ANEXT` ⇒ 认定它是 `else` 落点」）。
  编排方从落地字节**重新派生**并与 A2 提案逐字节比对相同（`logs/tool_mk_spec34e.py` 输出的
  `byte-for-byte identical to A2 proposal: True`），anchor 唯一（第 4494 行），引用的每个符号
  都在同一作用域内已被既有代码使用，候选文本 `compile()` 通过。
  `region_analyzer.py` 无 BOM、纯 CRLF、正规化 sha256[:20] `2f7c18c2e7b7e3851a2b` == HEAD blob。
* **G1**（deficit-1 池）：`SAME=6 IMPROVED=0 REGRESSED=0` ＋ 靶子
  `default_event_source.pyc 13/14` 的 `events 510/508 j2 t157 → 510/509 j2 t155`（取回 1 条，
  文件不翻转）。读数 `logs/r34e_cand_d1.txt`。
* **G2′**（39 合成复现）：`SAME=37 IMPROVED=0 REGRESSION=2 MOVED=0 ERR=0`，
  `files fully matched a=28 b=26` —— 回退是**已固定**的
  `round4/r4_06_continue_after_nested_for_dropped.pyc 2/2 → 1/2`（`f 56/55 j3 t19`）与
  `r4_07_continue_after_two_nested_fors.pyc 2/2 → 1/2`（`f 84/83 j3 t25`）；单件重跑复现，
  非分片伪影。代理自己在 104 锚点上的 A/B 也独立给出 `SAME=99 REGRESSION=4 MOVED=1`
  （`logs/r34e_agent_g3_ab.txt`，A2 产物，编排方仅存档）。⇒ 电池尺 FAIL，**不进入 G3／G4**。
* 只读探针（`logs/tool_probe_else34.py` → `logs/probe_else34_landed.txt`）把六条相关块并排量出：
  加一条出路事实（「`eb` 尾指令是跳向别的环头的回边」）能一次排除 `r4_06`／`r4_07` 的两条
  `continue` 落点，但 `r4_07` 的**兄弟环 `GET_ITER` 块**与靶子真正想取的 `else` 落点在全部
  可读结构事实上同形。原因在字节码层：

  > `for …: else: S` 与「子环后紧跟同一条语句 `S`」在 `S` 本就紧随其后的场合编译出**同一个 CFG** ——
  > `FOR_ITER` 的耗尽边目标就是 `S` 的块。

  ⇒ 「只在正常耗尽时进入」既不能证明也不能否证 `else` 的存在；落地的
  「`eb ∈ parent_body` ⇒ 判为 spurious」是有意的启发式取舍（Round 30 R30-C1 同族），
  任何只读入边/出边的同层判据去推翻它都会把「没有 else」的落点补成 else。
  靶子 `events` 的残余（1 条指令＋2 个跳转槽）据此**改判为字节码层欠定**，
  并把 Round 31 §六「需两条判据」订正为：第二条不在归属侧也不在发射侧，而在
  「是否有资格宣称 else」这个不可判前提上。

## 四、线 A（代理 A1 → 编排方接手）：根因链闭合到站点，但附带损伤已知 ⇒ 让位 Round 35

一手证据（全部由编排方自己重跑，见 `arm-design.md` §五）：

1. `function.pyc :: save_testds_to_json` 的 code object 里
   `@1976 POP_EXCEPT / @1978 POP_EXCEPT / @1980 LOAD_CONST(None) / @1982 RETURN_VALUE`
   就是唯一缺失的四条（也与原始异常表多出的 `start=1976 end=1978 target=1994 depth=1` 同段）。
2. 落地产物该函数只有两条 `return None`（最内层 `try` 体尾、最外层 handler 体尾），
   **函数级终止 `return None` 一条都没有**。
3. 站点：`region_ast_generator.py:24687-24694` 会给「本身在 `handler_blocks` 里、
   role=RETURN」的块就地发 `Return(None)`；越过 handler 边界**只**看一跳的 R13 后继扫描
   `:24707-24734` 只有 CONTINUE/BREAK 两条臂，且还要求后继块属于某 `has_finally` 区域的
   `finally_copy_blocks`。靶子的 `@1956 → @1976`（纯 `POP_EXCEPT` 清理块）两条臂都不进，
   于是 `@1976`、`@1978` 成对沦为孤儿 BASIC 区域（`R19`/`R20`，父区域 members 不含），
   整条退出路径无落点。
4. 候选 R35-A（**本轮未写未测**）：给该后继扫描加第三条臂 —— 沿既有 `_cleanup_only_ops`
   白名单（`_is_cleanup_only_no_return`，`:25496`）穿过纯清理块直到过滤后恰为
   `LOAD_CONST(None)+RETURN_VALUE` 的块，补发 `Return(None)` 并把链上块记入 `generated_blocks`。
5. 不发货的理由是**已量出的附带损伤**：A1 的语料级产物侧剥离实验（46 个文件里 79 个以
   `return None` 收尾的函数，8 片 `logs/corpus_drop.f*.jsonl`，汇总 `logs/corpus_drop_summary.txt`）
   显示该靶子
   `delta −4 → 0`，同时 `instance.pyc :: _get_manage_info 0 → +1`、
   `trade_info_utils.pyc :: query_trade_strategy_info`（转为有缺陷）、
   `query_strategy_id 0 → −1`。⇒ R35-A 必须先有「该清理链是否就是函数唯一收尾出口」这一同层守卫，
   再谈门禁；带着已知附带损伤去跑 G4 不是裁决，是赌博。

## 五、方法论收获

1. **电池先于语料**再次兑现：R34-E 在 G1（语料靶子）上净收益、在 G2′（合成复现）上破两个
   已固定形状 —— 只看 G1 就会把它当候选送进 G4。本轮省下的是全量 402 A/B 与一次回滚。
2. 代理线的**上限**是结构性的：两条线各用满 150 轮次／157、181 次工具调用，都没交出
   `ANALYSIS.md`，但都交出了可复用的一手测量（A1 的语料剥离表、A2 的候选与 `em_r406_*` 转储）。
    ⇒ 后续轮次把「语料级附带损伤扫描」从代理任务里剥出来由编排方自己跑，
   给代理的交付物压缩成「一个函数 + 一个站点」的单选题。
3. 「不可判」也是一条可交付结论：把它写清（§三 的引文）比再试第三个变体更省未来轮次。
4. 本轮**没有**新增 `*OK.py` 文本变化、没有 `MOVED`、没有索引改动，因此不存在
   「ok 文件产物文本变化」在册观察项的新增。

## 六、移交 Round 35

1. **R35-A**（首选，根因链已闭合）：线 A 的清理链 → 裸 `return None` 发射臂；
   先决条件是那条「唯一收尾出口」同层守卫，须先把 `_get_manage_info`／
   `query_trade_strategy_info`／`query_strategy_id` 三例挡在判据外（可用 A1 的
   `corpus_drop` 尺子先做产物侧预筛，再写真判据）。靶子 `function.pyc 14/15 → 15/15`。
2. `default_event_source.pyc :: events 510/508 j2 t157` —— **改判为字节码层欠定**，
   除非找到非「入边/出边」层的同层事实，否则不要再从 else 归属侧进攻；
   R34-E／R34-F 两个变体均已否证（`logs/r34e_*`、`logs/probe_else34_landed.txt`）。
3. 残余 deficit-1 六个未动：`instance 31/32`（`_init_config 86/84`，R16 J1 在册反例，受保护）、
   `replace_utils 8/9`（`decrypt_database_url 295/324`）、`strategy 23/24`
   （`tick_worker_thread 268/247`）、`realtime_event_source 11/12`（`clock_worker 1275/1291`）、
   `matcher 16/17`（`match 713/689`）；`default_event_source 13/14` 与 `function 14/15`
   分别见本文件 §三／§四。**本轮七个 deficit-1 文件全部逐字节未变**（G1 `SAME=6` ＋ 靶子
   只有 `events` 所在文件被候选触及，候选未落地）。
4. #61 R30-B3 ＋ 语料外见证 `r29x_01 <module> 142/138` 继续在册。
5. 锚点新要求：Round 35 电池 = `anchors104.txt`（本轮已建，无新增承重件）＋ 若 R35-A 落地则
   ＋ 其见证；`reprobat39.txt` 同现沿用。合成件 `py_compile` 必须显式传 `cfile`。
6. 基线复用：本轮的 `head` 臂 402 读数（`logs/g4_head.all.jsonl`）就是下一轮的 G4「改前」侧，
   只要下一轮开工前核未动（sha `2d3a5d51d114da77d3d4`）即可直接比对，省去一次 402 复测。

# FINDING — rr-v5r131 [v131-SWAPASSIGN]：DEREF 目标 SWAP N 源序元组赋值还原（REAL46-011 NormalDist.samples×2 闭合，真实 R1）

## 0. 结论速览

- REAL46-011 余 3 差单元中的 **NormalDist.samples + 其 <listcomp>**（2
  单元）本轮修复：`mu, sigma = self._mu, self._sigma`（DEREF/cell 目标）
  渲染为 `mu = self._mu`——**sigma 赋值整条丢失**，listcomp 闭包引用
  sigma → 运行时 NameError（**真实 R1 语义缺陷**，非字节差）。
- 缺陷位点 = `_build_statements_from_instructions` 的 B234-V3R38 定长多
  目标归约守卫②显式排除 SWAP——本 walk 不跳过 SWAP（与主 walk
  SKIP_OPS 不同），SWAP 累积进 stmt_instrs 使守卫恒拒：首 STORE 把整段
  当单一 RHS 重建（SWAP 被当链式比较协议吞掉部分值）、次级 STORE 缓冲
  已空返回 None → 整条赋值静默丢目标。主 walk SIG2 已有 R68-b2 cell-
  swap 分支（SWAP 在块内不入缓冲、按块内指令识别），本 walk 无对应分
  支=缺口。
- [v131-SWAPASSIGN] 单文件 +56/−0（只增不破）：B234 归约前新增 SWAP N
  源序形分支——连续 STORE 段 N>=2 且累积值段去噪尾指令为
  SWAP(arg==N) → 值段剥 SWAP 整栈重建（栈序=压栈源序）、目标按 STORE
  源序，Assign(Tuple(源序), Tuple(压栈序))。
- 修复后：statistics 判官 **74/77→76/77（98.70%）**（NormalDist.samples
  ×2 全消）；余 harmonic_mean（Different control flow）=else 压平独立
  族另登记（§5）。

## 1. 根因（三层追踪）

- 复现（repro3 = NormalDist.samples 精确形）：method 内前置三元
  `gauss = random.gauss if seed is None else ...` + `mu, sigma =
  self._mu, self._sigma`（DEREF 目标）+ listcomp 闭包。HEAD 产物丢
  sigma 赋值。
- 字节码形态辨析（I.4 实测）：定长元组赋值在 3.11 有三形——
  ① FAST/NAME 目标：`<e1>..<eN> STORE tN..t1`（**反源序**，无 SWAP，
  peephole 覆盖，B234/SIG2 已修）；
  ② DEREF 目标：`<e1>..<eN> SWAP N STORE t1..tN`（**源序**，peephole
  不覆盖 cell 存储——samples 实测 SWAP 2）；
  ③ 常量折叠：BUILD_TUPLE+UNPACK_SEQUENCE（既有 UNPACK 分支）。
  形②仅在主 walk 有 R68-b2 处理（SWAP 在块内、SKIP_OPS 不入缓冲、按
  块内指令序识别）；`_build_statements_from_instructions`（三元邻接前
  导区等上下文）不跳 SWAP → SWAP 入缓冲 → B234 守卫②排除 → 落
  `_build_store_statement` 整段当单一 RHS → 丢目标。
- trace 实证：SWAP store 调用自 `_generate_ternary:59257 →
  _build_statements_from_instructions:42799`（前置三元区域吸收整块，
  元组赋值在该 walk 的 stmt_instrs 中含 SWAP）。
- 3.11 SWAP N 语义：SWAP N 交换 TOS 与 TOS-depth N——N 个值压栈后
  SWAP N 把最深首值顶到 TOS → 后随 N 个 STORE 按源序弹出。

## 2. 修复（[v131-SWAPASSIGN]，只增不破，单文件 +56/−0）

`_build_statements_from_instructions` 的 B234 归约段前新增 SWAP 源序形
分支：连续简单名 STORE 段 N>=2 且去噪值段尾指令为 SWAP(arg==N) → 值
段剥 SWAP 后整栈重建（栈序=压栈源序）、目标按 STORE 源序（不反转）、
`Assign(Tuple(源序目标), Tuple(压栈序值))`；`_bsi_skip_until` 跳过被吸
并次级 STORE。与主 walk SIG2 的 R68-b2 同语义（C2，彼处 SWAP 在块内
不在缓冲）；重编译元组字面量赋值重新生成 SWAP N+源序 STORE 复现原字
节码。未命中（无 SWAP/arg 不匹配/重建失败）逐位落回既有路径（C3）。

## 3. 验证（全实测）

- **矩阵 8 案**（matrix_v5r131.py，A/B 单文件 RAG 交换 HEAD b871aea4
  vs v131）：E1 DEREF+listcomp 闭包+前置三元（NormalDist.samples 精确
  形）HEAD TEXT-DIFF→v131 **BYTE-EQUAL PASS**；E2 DEREF 普通方法体/
  E3 DEREF 三目标实测 HEAD 本已等价（走主 walk R68-b2，归控制零漂移
  证据）+C1 FAST 反源序+C2 FAST 三目标+C3 单目标 DEREF+C4 常量
  UNPACK 形+C5 DEREF+UNPACK 全零漂移。**MATRIX: ALL PASS**。
- **REAL46 判官触达**：statistics **74/77→76/77（96.10%→98.70%）**——
  NormalDist.samples + <listcomp> 2 单元全消（module byte_equal 实证
  repro3 重编译）。
- **A/B 电池 267 案**（r131_regress.py，单文件 RAG 交换 HEAD b871aea4
  vs v131）：**TEXT-DIFF 0/267**（全语料零漂移——SWAP 源序形分支仅在
  连续 STORE 段 N>=2 且值段尾 SWAP(arg==N) 时触发，267 语料零触发=外
  科性）；R110 168/169 一致（mc1 正常归一）；登记差 10 案 **ALL
  SAME-SIGNATURE**（含 SUBST-SIG pd8_prod）；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（与基线逐项一致，
  余 2 失败=冻结对 B01/BOUNDARY_02）。
- **REAL46 全量 sweep 豁免（小修口径）**：statistics 新鲜判官读数直接
  覆盖触达面（76/77）；回归面由电池 267 案零漂移+矩阵 7 控制案兜底。

## 4. 验收口径

实测读数同 §3：statistics **74/77→76/77（96.10%→98.70%）**（REAL46-011
余差仅剩 harmonic_mean 他族）；电池 267 案 TEXT-DIFF 0；pytest 冻结对
基线一致。不宣称 G1/G2c/G3/G4/G6 通过；product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. **harmonic_mean else 压平族（本轮诊断未修）**：源码 `if weights is
   None: … else: <嵌套 if> <嵌套 if>` 渲染为 `elif weights is None: …`
   + else 臂嵌套 if 压平进顺序流（控制流/字节差 R2；语义侥幸等价——
   repeat 对象自身是迭代器且 list(repeat(1,n)) 长度恰为 n）——if/elif
   链 else 臂嵌套区域保持族，statistics 余 1 单元。
2. REAL46-012 difflib（53/62）/014 tarfile（142/160）/016 urllib.request
   （185/194）未触达族；4 compile_error；pytest 余 2 冻结对（登记态）。

## 6. 证据文件

`fix_patch_v5r131.diff`（+56 单文件）、`matrix_v5r131.py`+result、
`repro3_src.py`/`product_HEAD_repro3.py`/`product_v131_repro3.py`（最
小复现双态产物）、`r131_regress.py`+result、本文件；中间件
D:/temp/opencode/cl_layout/r130diag、r131matrix、r131regress 不入库。

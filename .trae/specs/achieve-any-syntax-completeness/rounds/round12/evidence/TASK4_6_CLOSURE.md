# Task 4.6 封闭记录：deephost-001 match 臂锚 +1 NOP（R12-MATCHANCHOR）

日期：2026-10-24。前置：4.1–4.4 四族修复（6d60cba0/607089e8/0df50457/280d2c59/
1ff5d40a）+ 023 条件变体与 015 dict `**` 家族（1ff5d40a）后 fuzz 23/24，唯一
残差 FZ-deephost-001（strict R7 main co_code.len 414→416，pyc_verify 2/2）。

## 一、根因（实测，非推测）

原件源码 `case _: raise ValueError(i)`：CPython 3.11 match 语句为每个显式
case 臂的体入口发射 NOP 结构标记（region_analyzer
`_mr_block_has_explicit_case_marker` 判据：前导 POP_TOP/噪声后首个非噪声指令
为 NOP；deephost-001 main 中 NOP@158，行位= `case _:` 行）。

臂体块 blk@158 = [NOP@158, LOAD_GLOBAL@160, …, RAISE_VARARGS] 由
`_generate_match` 的 B141/try 路径委托 `_generate_block_statements`（仪表实测
`DBGTRY blk@158`），其中行头游程解析分支（`_is_unaccounted_folded_head_nop`）
命中 NOP@158，从未引用常量队列取 0 发射 `while 0: pass` 幻影单元 →
重编译 = 臂锚 NOP（match 源码重编译自然再生）+ while NOP = +1。

排除记录（对照实验）：锚点经头判据 veto → 落入孤儿分支同游程解析吞
`LOAD_GLOBAL ValueError`（`raise` 头被当包裹测试）→ 臂装配坍缩 186/414；
裸 Pass 占位分支与解析器单元换形均坍缩。坍缩根因即「标记被消费后臂体首指令
失位」，故正确解法是剥离标记而不是替换占位。

## 二、修复（family 级）

`region_ast_generator._match_arm_entry_block_without_marker(block)`：臂入口块
（`region.case_bodies[i][0]`）携带 case 标记时，构建剥离该 NOP 的虚拟块（前导
POP_TOP/噪声保留、后继语句段原序）交语句生成；非入口/无标记块原样返回。接入
`_generate_match` 两处委托（B141/try 路径 + 普通块路径），臂入口 id 集在 case
循环前按 `case_bodies` 一次性计算。

I.4 白名单：判据只读块指令序（`_mr_block_has_explicit_case_marker` 结构事实）
+ `case_bodies` 成员关系；无偏移/名字/语料特例；[C1] 局部只读、[C2] 虚拟块仅
替换本次委托入参、原块 generated 登记不变、[C3] 编译器按 case 发射的结构标记
与 case 位置/嵌套深度无关。

## 三、验证

- deephost-001 全量：pyc_verify 2/2；strict 全单位 co_code sha 全等
  （main 414=414）且各单位非代码 co_consts 全等。
- 合成探针 `probes_fz/p_fz_families.py`（4.1 unpack 值段切分 / 4.2 send 绑定 /
  4.3 posonly 签名 / 4.4 条件 return-in-finally 四族 + main）：pyc_verify 7/7，
  `semantic_p_fz_families.json` EQUAL（调用级 case 含 fz3 两种实参形）。
- x01 探针 v1–v5：pyc_verify 7/7、semantic_diff EQUAL（回归确认游程解析族
  无回退）。
- 023/015 最小复现：pyc_verify 2/2、2/2。
- B142 定向：p_g1_fin_paths 3/3、p_g2_loopctrl 2/3、p_g3_double_fin 2/3——与
  冻结基线逐位持平（TASK3_1_X01_REPRO.md 记录基线即 p_g2 2/3、p_g3 2/3，
  失配单元 g2_brk/g3_three_fin 属 B142 第 4/5 项出口终结符物化族，Task 2
  挂账在案，非本次改动引入——对照实验 be256ae0…a5c84364 全序列同值）。
- 402 shard0 786/786、small34 1568/1568、quotation 153/153、签名校验器 14 错
  误基线持平、pytest 全量（--ignore=tests/nook，与基线口径一致）失败清单
  与 406 项基线逐字节一致。
- fuzz 复跑 24 条：24/24 EQUAL（fuzz_summary.json）。

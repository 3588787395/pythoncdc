# FINDING — rr-v5r116 [v116-FOLDRET]：编译器折叠隐式臂返回误渲染为显式 return None（co_consts 驻留序破坏族）+ REAL46-019 盲区 3→1

## 0. 结论速览

- REAL46-019（ipaddress）判官盲区 3 差异（rr-v5r114/r115 登记）→ **闭合 2**：
  `/IPv4Network/__init__` 与 `/IPv6Network/__init__`（co_code 等长不同字节 +
  co_consts 驻留序互换）。全嵌套递归字段比对 166 code objects：**3 → 1**。
- 剩余 1：`/_BaseNetwork/address_exclude`（co_code 762 vs 718，缺 44 字节）——
  本轮精确定性、登记下轮（§5）。

## 1. 根因（settrace/逐指令比对 + starts_line 判别器）

### 1.1 差异面

`IPv4Network.__init__` 尾部源码：

```python
        if self._prefixlen == (self._max_prefixlen - 1):
            self.hosts = self.__iter__
        elif self._prefixlen == (self._max_prefixlen):
            self.hosts = lambda: [IPv4Address(addr)]
```

原件 pyc（编译器视角）：

```
426 LOAD_FAST self; 428 STORE_ATTR hosts        ← if 臂体
438 LOAD_CONST None(starts_line=None); 440 RETURN_VALUE   ← 折叠对
442-472 elif test … POP_JUMP_FORWARD_IF_FALSE 498
474-484 LOAD_CLOSURE addr; LOAD_CONST <lambda>; MAKE_FUNCTION; STORE_ATTR hosts
494 LOAD_CONST None(starts_line=None); 496 RETURN_VALUE   ← 折叠对
498 LOAD_CONST None(starts_line=1524); 500 RETURN_VALUE   ← 函数尾声（带行标记）
```

- 折叠对成因：if/elif 链为函数末语句，各臂体结尾的 JUMP_FORWARD（跳向紧随
  的函数尾声 LOAD_CONST None + RETURN_VALUE）被 CPython 3.11 优化器 jump-
  threading 穿线为内联 [LOAD_CONST None, RETURN_VALUE]。**该对非源码语句**
  （LOAD_CONST 的 starts_line=None；源码 return 的 LOAD_CONST 行标记必非
  None——repro1/repro4 实测 @7/8/14/15/17 全有行号）。
- co_consts 驻留序：原件 None 在优化期（lambda 常量已驻留之后）才首次入表 →
  `[doc, msg, 1, <lambda>@3, None@4]`；产品把折叠对渲染成显式 `return None`
  语句 → None 在 if 臂语句序提前驻留 → `[doc, msg, 1, None@3, <lambda>@4]`
  → 4 字节 LOAD_CONST oparg 全反（438/478/494/498）。

### 1.2 既有判据缺口

- BSS-body 主循环 RETURN 处理器的 `_r23n16_ret_flag`（[W14-B]）：分支内裸
  return 以 `_w14_has_following_code`（块后仍有可达代码）背书 explicit——
  本形 elif 兄弟臂在**假边**可达 → 误判 explicit → 显式渲染。
- 判别器（全同层结构事实）：RETURN 紧前 LOAD_CONST None 的 **starts_line
  是否为 None**。None ⇒ 折叠产物；有行号 ⇒ 源码 return（v115 [BARERET] 族，
  必须保留渲染）。

## 2. 修复（region_ast_generator 只增不破，[v116-FOLDRET] 单 hunk）

BSS-body 主循环 RETURN_VALUE 处理器头部（`<module>` 分支之后、W14-B 标记
之前）新增折叠对守卫：

- 条件：`stmt_instrs` 恰为单个 `LOAD_CONST None` 且其 `starts_line is None`
  （纯折叠尾对；带值 return / 源码 return / RETURN_CONST 不命中）；
- 且本块非函数尾声块（`block.start_offset != max(cfg.blocks.start_offset)`——
  尾声块的 Return 交函数尾既有 strip/物化机制处置，此处误杀会打乱
  `_build_function_def` 尾段约定，首轮实测 `_IPAddressBase` 全属性方法爆炸
  回归后收窄）；
- 且**非生成器函数**（`self.cfg.code.co_flags & 0x20` 为 0）——生成器内折叠对
  （yield 附近 jump-threading）的重编译**不复原**：mk_iterencode `_iterencode`
  实测丢弃后重编译缺内联对、签名 DIFF（首轮电池捕获回归后收窄）；
- 命中 → 跳过 Return 发射（`stmt_instrs=[]; continue`），臂自然落空，重编译
  由同一优化器折叠再生（3.11.7 钉版）。

过程登记：①首轮误实施（守卫置于 `_r23n16_in_except` 定义之前 → folded 命中
时 NameError → generate() 顶层兜底吞异常整函数降级重建，_IPAddressBase 全爆；
同时误改 BSI RETURN 处理器无尾声守卫）——回退修正；②次轮电池捕获生成器回归
（mk_iterencode `_iterencode` 签名 DIFF）→ 增补③生成器收窄。另：电池脚本
标记串替换链两次产生奇美拉断言（v116-ARGOR/v116-BARERET）+ r116 误用 r115
TMP 目录致 decompile_cached 产物污染——均已修正后干净重跑，本节读数为最终
实测。

## 3. 验证（全实测）

### 3.1 变体矩阵（`matrix_v5r116.py` 4 案，A/B HEAD `2fdc1ceb` vs v116）

| 案 | 形 | HEAD | v116 | 判定 |
|---|---|---|---|---|
| E1_foldret_lambda | if/elif + lambda + 折叠对（IPv4.__init__ 同构） | TEXT-DIFF | BYTE-EQUAL | PASS |
| E2_foldret_consts | 三臂 elif + lambda + 折叠对（多常量驻留序） | TEXT-DIFF | BYTE-EQUAL | PASS |
| C1_src_ret | 源码 return 形（repro4 同构，行标记在） | 逐字节同 | BYTE-EQUAL | PASS-C3 |
| C2_src_ret_nested | 源码 bare return 嵌套（repro1 同构；内含折叠对 @392） | TEXT-DIFF | BYTE-EQUAL | PASS（折叠对正确丢弃，文本更贴近原源码形） |

### 3.2 REAL46-019 盲区（`field019.py`，166 code objects 递归比对）

- v115：3 差异 → v116：**1 差异**（仅剩 address_exclude）。
- 判官维持 **EQUAL（diffs=0）**（盲区差异本就不进判官，无 verdict 变化）。

### 3.3 回归

- v115 全部复现（repro1/repro3/repro4）修复后重验 **BYTE-EQUAL**（源码 return
  形不受判别器影响）。
- A/B 回归电池（r116_regress.py：r110 169 + v111 15 + v112 15 + v113 15 +
  v115 9 + v114 12 + 本轮 4 案源，独立 TMP 干净重跑）：**TEXT-DIFF 4 / 227**，
  恰为本轮 2 功效案（E1/E2_foldret）+ v115 功效案 E2_bare_ret_nested +
  C2_src_ret_nested（折叠对正确丢弃的改善），全部重编译 BYTE-EQUAL；
  mk_iterencode（v116 首轮回归案）生成器收窄后恢复 TEXT-SAME；既有登记差
  10 案 **ALL SAME-SIGNATURE**；NO-SRC 0。
- pytest 7 套件冻结对一致；比较器 pyc_verify.py FE1902A9 / semantic_diff.py
  DBCB1E24 冻结一致、tests/ 零改动。

## 4. 验收口径

小测试收口（全量闸门按用户政策只留给大改动）。不宣称 G1/G2c/G3/G4/G6 通过；
product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选，未修）

- `/​_BaseNetwork/address_exclude`（co_code 762 vs 718，−44 字节）：源码
  `while` 循环内三臂链 `if other.subnet_of(s1): … elif other.subnet_of(s2):
  … else: raise`——产品把 **elif 臂折叠进 else 臂**（`elif` 测试指令消失，
  `yield s1; s1, s2 = s2.subnets()` 与 else 臂的 `raise AssertionError`
  顺序合并），生成器 while 循环内 if/elif 链分析域（Task 39 WYBREAK 同域
  另一形态）。**真实 R1 语义缺陷**：合法排除路径（subnet_of(s2) 成立）会
  误抛 AssertionError。
- E6 相邻 NOP 对；46 sweep 其余 DIFFERENT（REAL46-022 typing 36 维等 8 案）；
  46 sweep 17 ERROR。

## 6. 证据文件

`fix_patch_v5r116.diff`、`matrix_v5r116.py`、`r116_regress.py+result`、
`field019.py`（盲区递归比对）、`semantic_REAL46-019_v115.json`、
`REAL46-019_v115.py`（产品）、本文件；中间产物一律
`D:/temp/opencode/cl_layout/r116diag|r116matrix/` 不入库。

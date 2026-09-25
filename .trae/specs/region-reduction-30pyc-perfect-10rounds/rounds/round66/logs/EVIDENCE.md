# Round 66 — 集中验证记录（EVIDENCE）

约定：ROOT = `D:/Temp/opencode/r66gate`（六批私有工作区）与 `ROOT/center`（主代理集中验证）。
所有命令 `python -X utf8`，不设 `PYTHONIOENCODING`；核心文件一律按字节补丁并保留 BOM/CRLF；
仓库侧只读，直到 §E 的落地步骤才写 `core/`。

## A. 轮初基线是可复放的，不是自报的

`center/dump/l402_all.jsonl`（`--arm=landed`，4 分片，每片 < 24 s）：402 条记录，matched
**5693/5746**，完全匹配文件 **385**，errors 0。`center/audit66.py` 对 HEAD 的 `pyc_index.json`
逐条比对：条目不在 dump = 0、dump 路径不在索引 = 0、**逐字段不一致 = 0**
（比较 `matched_functions` / `function_count` / `decompile_status`）⇒ 轮初工作树字节与已提交索引
一致，基线不是自报数字。

电池 24 项 `center/dump/battery_landed.jsonl`：matched **91/104**、全清 17。
金丝雀 4 项 `center/dump/canary_landed.jsonl`：143/143、10/10、26/26、25/25，产物 sha
`4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177`。
严格尺（17 支 partial）`center/dump/strict_landed17.json`：**672/749**，77 个缺陷
（51 seq_len / 18 target_diff / 8 seq_diff）。

## B. 候选体检：8 份 spec 全部对 R65 落地字节干净应用

| spec | 文件 | anchor 落地行号 | `count==1` | build 断言 |
|---|---|---|---|---|
| `diag6/specs/cand_r66_iterpre_del.json` | generator | L7212 | ✓ | 镜像 == 工作树，BOM ✓，CRLF ✓ |
| `diag1/specs/cand_r66_e1.json` | generator | L16843-16850 | ✓ | 同上 |
| `diag5/specs/cand_r66_trytail_else.json` | generator | L26554 | ✓ | 同上 |
| `diag4/specs/cand_r66_d1_augsub_continue.json` | generator | L44369-44371 | ✓ | 同上 |
| `diag2/specs/cand_r66_p4_chainhead_owner.json` | generator | L16985 | ✓ | 同上 |
| `diag2/quarantine/hold_r66_p3_prefixparts.json` | generator | L36179 | ✓ | 同上 |
| `diag2/specs/cand_r66_p1_namecallee.json` | generator | L41454 | ✓ | 同上 |
| `diag3/specs/cand_r66_diag3.json` | **analyzer** | L20948-20949 | ✓ | 同上（analyzer 无 BOM） |

符号核对（主代理在采纳前逐个 grep，见 memory `verify-subagent-symbols-before-adopting`）：
`_build_delete_stmt` def L47882 / 8 个调用点，DELETE 终止符已在 L2856、L5706、L8931 存在；
`_w11_unprotected_else_candidate` def `region_analyzer.py` L10360，签名 `(try_region, block)`，
`self.region_analyzer` 在生成器里被用 345 次 ⇒ 跨对象调用是既有通道；
`_split_subscr_operands` def L2624、`_build_subscript_assign` def L49198；
`IfRegion.chained_compare_blocks` 是真字段（analyzer L372）；
diag3 侧另有 `FORWARD_CONDITIONAL_JUMP_OPS` L37、`NOISE_OPS` L60、`can_be_ternary_header` L457、
`_can_be_ternary_header` L20253、`_detect_ternary_pattern` L20932（缩进 8 ⇒ 嵌套于
`_identify_ternary_regions`）、`_is_single_expression_block` L2781、
`get_last_instruction` = `core/cfg/basic_block.py` L132。

## C. 逐批判定（代理自述 + 主代理复测；被推翻的写在最右列）

### C.1 diag6（`common_func` 20/21）——采纳 A
唯一「修到完全 OK」候选。主代理单臂复测（`dump/d6_landed.jsonl` vs `dump/d6aug.jsonl`，
该批靶子集 6 条）：`SAME=5 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`，完全匹配文件 0→1；
复现 1/3→3/3。判据是「同一条直线块语句流的语句边界终止符集合缺一类」，同文件另有三处已有
DELETE 终止符作同层佐证 ⇒ 不是新发明而是补齐异类。全 17 支与 402 的加和证据在 §D 的合并集门禁里。

### C.2 diag4（`risk_calculation` 32/35）——采纳 D1
`get_TradeMode_trades` 的 CONTINUE 角色块走的是另一个 STORE_SUBSCR 分裂器，缺 `[R102 fix]`
的读回协议判据。移植而非新写：委托既有 `_build_subscript_assign`。主代理单臂复测
（靶子集 3 条）`SAME=2 IMPROVED=1 REGRESSION=0`，读数 32/35→33/35、严格 33/37→34/37、
复现 1/2→2/2。同批 `_do_request` / `order_api` 不采纳（§6）。

### C.3 diag5（`scheduler` 43/45）——采纳 B
try 体尾部、保护跨度之外的 `else`：CPython 3.11 把 `try/except/else` 的 else 体放在
`[try_offset_end, first_handler_entry)`，代理用异常表实测证明；主代理核对
`_w11_unprotected_else_candidate` 存在且签名匹配后采纳。单臂复测（靶子集 4 条）
`SAME=3 IMPROVED=1 REGRESSION=0`，读数 43/45→44/45、严格 49/52→50/52、复现 2/3→3/3。
同批 `fileio_utils::write`、`params_analysis` 不采纳。

### C.4 diag1（`trade_live_broker` 106/119）——采纳 E1，否决其 variant-1
E1 把「本臂无语句」这条既有过滤器原样作用到区域自身的 `else_blocks`，再加
`chained_compare_blocks` 为空 ⇒ 唯一可能的源码形状是 `if cond: pass` + 非空 else
（3.11 的 `pass` 发 0 条指令）。107/119、复现 2/3→3/3。
**variant-1（去掉 `chained_compare_blocks` 条款）在 402 上把 `strategy.pyc` 24/24→23/24**：
24 项电池完全没抓到，402 抓到 ⇒ 印证「电池先于语料、但 402 不可省」。

### C.5 diag2（`quote.pyc` 70/81 + R65 遗留）——采纳 P4 + P3 + P1；代理被轮次上限杀掉
诊断本体（FACTS §2）用三条独立测量证明重复发射机制：发射台账出现 2 份 SAME-DICT 语句、
区域状态快照 `PRE mask=GGGG gen_id=False`（块级已认领而区域 id 未认领）、异常注入消融让第二份
消失。P4 即把守卫从「区域 id」换成「区域自身的 blocks 登记状态」。
**实测更正代理前提**：`_generate_chain_head_prefix_assign` 在整个测量集合里只有 `quote.pyc`
调用过（1 次），fs2/fsrepro/24 项电池/3 支合成都为 0 次 ⇒ 「修重复发射就能让 fs2 10/10」不成立，
fs2 的五支残余属前缀扫描族（P3/P1 的靶）。合成复现两次都没能重造该形状（回退链发现只在 merge
块同时带模块级名字与调用形状时才触及共享模式），故该候选的证据是产物级 hunk 表（58→7 指令）
与台账，而不是合成件——这一点如实记录，不算复现门通过。

### C.6 diag3（`real_quote` + `klinedata`，8 支）——采纳 1 支（唯一动 analyzer 的编辑）；代理同样被杀
`[R24-A]` 在 `IfRegion.can_be_ternary_header`（L457-471）的最后一条合取恰好拒掉
「条件块同时是 CFG 入口块的链式比较三元」。调用链实测：`_identify_ternary_regions`(20117) →
`_detect_ternary_pattern`(20932) → L20948 `if not _can_be_ternary_header(block): return None` →
`_can_be_ternary_header`(20253) → L20346 `existing.can_be_ternary_header(block, self)` → 拒。
后果按字节读出：两臂被发射为表达式语句、值被丢弃、汇合块的 `STORE_FAST data_count` 整条消失。
编辑是「撤销区域归属并交回 Phase-7-D 建 `TernaryRegion`」，四条结构合取 + 复查后可逐字回滚。
**为什么必须在 L20948 而不是通用重叠过滤器**：链区域在 phase 6 建立、同一 list 对象在 L1727-1730
装配、L1814 重指派给 `self.regions`；L1508-1531 的三元重叠过滤只作用 `match_regions`/
`assert_regions`，L1713-1725 的 IfRegion/BoolOp 去重被显式禁用（注释：曾因过度识别导致大面积
丢失）。所以被吞掉的链区域永远不会退役 ⇒ 落地臂仍会发射 `if 0 < int(data_count) <= 200: pass`。
这与 R65 的 BoolOp 链 pop 域（L25362/25574/25630/25748，settrace 计数在两臂皆 0）相隔 4600 行、
互不相干。
8 支里 6 支分类后判「无可落地判据」（位移族 3、发射顺序 2、编译器重入块 1），逐条排除证据在
`batches/diag3/FACTS.md` §2.2。

## D. 合并集的单变量实测（落地前）

`mkfinal66.py` 按落地字节偏移排序 + 链式 anchor 唯一性重放（每步断言 `count==1`），
`mbuild66.py` 建双臂镜像（断言 head 镜像==工作树、BOM、行尾统一、插入行数）。
中间臂保留：`m66`(3 edits) → `m66b`(4) → `m66d`(7) → `m66e`(7 + analyzer 1)。

| 门 | landed(R65) | m66e | 判定 |
|---|---|---|---|
| 17 支（官方） | 0 支全 OK | `SAME=11 IMPROVED=5 REGRESSION=0 MOVED=1 ERR=0` | 5 支上升，1 支全 OK |
| 电池 24 | 91/104，17 全清 | `IMPROVED=2 SAME=22 REGRESSION=0 MOVED=0`（fs2 5/10→6/10、fsrepro 6/7→7/7），全清 17→18 | 不变差 |
| 金丝雀 4 | 4 支 sha | `SAME=4`，四支 sha 逐字节不变 | 承重件未动 |
| R66 复现 7 | 12/23、0 全清 | **22/23、6 全清**，`IMPROVED=7 REGRESSION=0 MOVED=0` | 每处编辑落地后仍清自己的见证 |
| 402 A/B | 5693/5746，clean 385 | **5698/5746，clean 386**；`SAME=396 IMPROVED=5 REGRESSION=0 MOVED=1 ERR=0` | 4 分片，每片 < 24 s |
| Σ\|orig−decomp\| | 418 | **328** | −90 |
| Σ jumpdiff / Σ truediff | 196 / 11977 | **184 / 9405** | −12 / −2572 |
| 缺陷函数（402） | 53 | **48** | −5 |
| 产物 blast | — | `identical=396 changed=6 unresolved=0` | 变化集 == 6 支被触达文件 |
| 严格尺（17） | 672/749，77 缺陷 | **677/749**，72（47/18/7） | +5；**清空 5 个缺陷函数名，新增缺陷名 0**（4 行 `+NEW` 是同一函数的缺陷种类改判且缺口更小） |

## E. 落地与串行门禁

1. `land66.py land --spec=m66e_region_ast_generator.py.json --mirror=center/mirr_m66e`（先 dry run）
   ⇒ `replay == measured mirror bytes: OK (3140634 bytes)`；`--apply` ⇒
   `applied: 3123069 -> 3140634 bytes, CRLF 50626, BOM=True, equals measured mirror=True`。
   analyzer 同法：`1727576 -> 1734099 bytes, CRLF 27763, BOM=False`。
2. `closeout66.py landproof mirr_m66e` ⇒ **33 个 core 文件 same=33 diff=0**。
   两文件 `py_compile` + `ast.parse` 均通过。
3. G1 `single site-packages/IQCommon/util/common_func.pyc` ⇒ `ok`、**21/21、100.00%**、
   `missing_in_decomp=[]`、`extra_in_decomp=[]`；`common_funcOK.py` 由工具链重写（源 16366 字符）。
4. G2 `single fly/data/quotation.pyc` ⇒ **143/143 100.00%**（源 176722 字符）；
   `_r10_strict_check.py …/quotation.pyc` ⇒ **148/150** 且缺陷集逐字未变
   （`change_his_to_forward [target_diff] #250`、`get_trend [target_diff] #10`）；
   `single fly/common/market_time.pyc` ⇒ **10/10**，严格 **10/10**、文件级 1/1。
5. G3 `batch --index pyc_index.json --all --round 66` ⇒ **402 verified / 0 failed**、
   ok 385→**386**、partial 17→**16**。本轮未复现 R65 的「Failed to decompile」瞬时失败。
6. G4 `stats` ⇒ `total_functions 5746`、`matched_functions 5698`、`cumulative_match_rate 99.16%`。
7. G4′ `strict_repo66.py center/all17.txt`（读**仓库出货产物**）⇒ 17 支合计 **677/749**，
   `common_func` **22/22**、`matcher` 16/17、`quote` 等逐支同 §D；`missing=0 extra=0` 全部成立；
   **17/17 出货产物 sha == 落地前实测镜像产物**（`mirror-sha …=measured`，`!=measured` 计数 0）
   ⇒ 出货字节就是被测字节。原始输出 `logs/gate/G4p_strict_repo_r66.txt`。
8. G5 `audit5_g5.py`（`git show HEAD:pyc_index.json` vs 工作树，逐条字段比对）⇒
   402→402 条、增删 0、键形变 0、**仅轮次戳 397 条**、实质变化 **5 条**（OUTCOME §4 表）；
   status `{ok 385, partial 17}` → `{ok 386, partial 16}`。
9. G5′ 出货侧影响面 `git status --porcelain site-packages/` ⇒ 恰好 **6 份 `*OK.py`** 修改
   （5 支 IMPROVED + `quote.pyc`＝MOVED），其余 400 份逐字节不变；`numstat` 逐支为
   +1/0、+2/8、7/7、1/1、+2/1、+3/7，六份都做过人工标本核对（OUTCOME §4）。
10. G6 `closeout66.py battery head landed`（31 支复现 × 两臂）⇒ **9 项改善、0 项变差**，
    R63/R64 的 19 项老见证逐支读数不变，脚本自证
    「candidate columns worse-than-landed on 0 repro(s)」。
    落地单列复跑 `logs/gate/G6_battery_landed_r66.txt`。
11. 全程未手改任何 `*OK.py`：G1/G2/G3 由工具链重写；提交前 `git status --porcelain site-packages/`
    中非 `*OK.py` 行为空。

## F. 本轮暴露的仪器问题

1. `closeout66.py` 的电池发现集靠 glob（R63/R64/R65 + 本轮新加的 `round66_*`），而仓库
   `.gitignore` 不收 `*.pyc` ⇒ 克隆后电池只剩 `shapes_r63.txt` 的 11 个 pinned 项。本轮已在
   `center/` 备 `r66repro7.txt` 显式清单，长期方案应是复现 `.pyc` 入库或每次构建前重编译。
2. `land66.py` / `strict_repo66.py` 的 `ROOT`/`GATE` 常量把「相对 `--mirror` 值」绑到 r66gate，
   而本轮全部镜像在 `center/`，导致一次 `../center/...` 形式的路径解析到
   `D:/Temp/opencode/center/...` 而 `FileNotFoundError`；改用 `center/mirr_m66e` 形式后正常。
3. `strict_repo66.py` 里写死的 `build_m65` 镜像产物目录已失效——本轮改指 `center/build_m66e` 后
   它反而变成一条有用证明（出货 == 被测）。这类硬编码应在脚本里参数化。
4. 子代理 150 轮上限连续两轮（R65 三支、R66 两支）砍掉交付：本轮两批的 FACTS/spec 完整但
   402 扫描没跑完，全部由主代理代跑。批次数与每批靶数应按「代理能在上限内跑完 402」来配。
5. `batch` 的瞬时 `RuntimeError: Failed to decompile`（R65 记录 3 支）本轮 0 次，仍未定位。

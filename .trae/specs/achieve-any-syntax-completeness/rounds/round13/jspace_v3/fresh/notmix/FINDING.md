# rr-v5r161 [v161-NOTMIX] 融合 not or→and 混合链族
# （REAL46-016 urllib.request 189→190/194）

## 功效案（urllib.request.FileHandler.open_local_file 实形，源 line 1514-1515）

```python
def open_local_file(self, req):
    host = req.host
    localfile = url2pathname(req.selector)
    if not host or (not port and self.get_host(localfile) in self.get_names()):
        return localfile
    raise URLError('file not on local host')
```

v160 渲染 `if host: if not port and ...:` ——factored 形=真实 R1（**语义反转**：
¬host 时源码返回 localfile、渲染落入 raise——本地文件无 host 时误报
URLError；判官 Different control flow）。r160 FINDING 已定向本族（open_local_file
与 redirect_request 同属 not-factored 语义反转族，v159 NOTCOND 修复未覆盖其
`not A or (B and C)` 融合混合链形）。

## 根因（r161diag 侦察存档：probe161/trace161/dis_olf + 七案最小化）

CPython 3.11 对 or 链首成员 `not A` 做**极性融合**——不发射 UNARY_NOT，直接以
POP_JUMP_FORWARD_IF_FALSE 直跳条件真值汇聚块（body）。or→and 混合链
`not A or (B and C)` 的操作数块 = [A IF_FALSE→body; B IF_FALSE→exit;
C IF_FALSE→exit]（c 实形第二成员 `not port` 为 IF_TRUE→exit）。主条件链走查
`_detect_boolop_conditional_chain` 的 opcode-only 分类把链首误标 'and'，三道
既有断链门都以「链首是真 and 头（其 FALSE 目标=共享 exit）」为前提斩断续接：

- b 形（FALSE 候选）死于 [W14-A 真/假出口目标对判据]（cand exit ≠ T0=body）；
- c 形（TRUE 候选）死于 [R3-K 读法 (b)]（候选真目标 exit ≠ 成功汇聚 T0）；
- 续接后的 and 子链成员死于 [R53-A 同算子 run 出口一致性]（run 头=链首、
  jt=body ≠ 成员 exit）。

链首走查死亡后 wrapper 从 B6 重试装配内层 and 区，链首 A 落入独立 IfRegion
→ `if a: if b and c:` factored 反转。三形复现（纯形 b/精确形 c/前导 if/try
包裹）均触发；最小形 `if not a or (b and c):` 即触发。

## 修复（只增不破，单文件，[v161-NOTMIX] 五处标记；含 fix161b 外科收窄）

`core/cfg/region_analyzer.py` `_detect_boolop_conditional_chain`：

1. 走查状态 `_v161_or_head_exit = None`（walk 循环前初始化）。
2. W14-A 门（b 形首续接）：首续接（len(chain)==1）候选与链首目标不等时，
   登记候选自身跳转目标 = and 子链共享 false-exit 并放行；后续成员目标与
   登记出口一致放行，不一致维持断链。
3. R3-K 门（c 形首续接）：TRUE 族候选同一甄别（负极性 and 子链成员
   `not X` 真=失败 → exit=子链共享 false-exit ≠ T0）。
4. R53-A 豁免：候选跳转目标与登记出口同块 = 该子链 run 的真实成员
   （与 _r53_same_run_exit 同一「run 头共享出口」判据，按正确 run 头
   chain[1] 计算）；不成立维持 pop（嵌套条件块不被吸收）。
5. 走查尾精确形甄别与重分类：**整链 ≥3（and 子链 ≥2 成员）** ∧ 链首
   'and'+FALSE 极性 ∧ 链首跳转目标 = 末成员 fall-through（条件真值 merge，
   `not A` 真边直达体的融合签名）∧ 其余成员跳转目标两两等价于登记出口
   （含 jump-threading 等价平凡出口变体）∧ 出口 ≠ 链首目标（歧义形维持
   原判）→ 链首重分类 'or'、子链成员统一 'and'（IF_TRUE 成员由构建层
   implicit-not 逐项还原 `not X`，与 W14-A 同目标归一同一理据）→ 既有
   or→and 边界 _try_unify 路径（`A or (B and C)` 判官 Equal 同构实证）。

**外科收窄（fix161b.py + fix161c.py）**：初版门/重分类守卫过宽，吞并两类
既有族，验收实证两处回归：

- **fix161b（C161_not_or 双成员纯 or 链）**：守卫 `len(chain) >= 2` 使
  `not a or b`（无 and 子链）也命中重分类 → 产物多 `else:` 分支（判官
  EQUAL 但文本风格漂移，违「零触碰」）。收窄 `>= 3`——本族目标是 or→and
  **混合**链（and 子链 ≥2 成员）；双成员链维持既有装配（矩阵复跑 SAME）。
- **fix161c（difflib NOTTAIL 族回归，61/62）**：v161 把 `group and not
  (len(group)==1 and group[0][0]=='equal')`（v148 NOTTAIL，`A and not (B
  and C)`）误渲染 `not (group and A and B)`——NOT 推进整个 and 链=德摩根
  语义反转（group 空时行为相反，判官 Different control flow）。根因=v161
  融合头甄别误作用于 NOTTAIL 链首 A（正极性真 and 头 IF_FALSE→exit，NOT
  在子链外层，非极性融合 not）。收窄=融合头甄别只认「链首极性融合 not
  （IF_FALSE→body=条件真值 merge，无 UNARY_NOT）」签名，NOTTAIL 链首排除
  （实证后定精确判据，I.4 白名单）。修复后 difflib 必须回 62/62。

两处收窄串行应用（同一实现子代理，避免并发改文件）；三门登记/放行核心
逻辑不变，仅收紧准入签名。功效案（E161 六案）产物不得漂移。

**fix161b 实证被推翻并裁决回退（narrow_check_result.txt 8/9 + 字节码）**：
fix161b 应用后 9 案中 a_not_or 恶化为**语义回归**——反汇编实证 `not a or
b` 被 CPython 极性融合（链首 a 的 FALSE 边直达 body，无 UNARY_NOT；b 的
FALSE 边→exit），line_analyzer 按「末成员 FALSE 极性」把链首误标 'and'
→ fix161b `>=3` 守卫排除重分类后产品渲染 `if a and b:`（a 假时源码进体、
产品跳过，真值表反转）。结论：HEAD 对双成员融合链的正确渲染靠的是「门不
放行→走查尾 None→wrapper 重试→HEAD 同构装配」路径；v161 门放行+重分类
是 a_not_or 判官 EQUAL 的承载者，`>=3` 守卫与 a_not_or SAME 数学互斥。
裁决：(B) 回退 fix161b（恢复 fix161-only +103/−3 状态）。

**两树探针实证（probe3.py，runpy 跑真实 pycdc 管线 + instrument 链检测；
DESIGN_r161c.md）—— fix161c 最终形态的依据**：

| 案 | HEAD 树 | v161 树 |
|---|---|---|
| `not a or (b and c)` | @0 → None；重试 @6 → [(6,and),(10,and)]（错误 factored 形） | [(0,or),(6,and),(10,and)] ✓ |
| `not a or b` | @0 → None；@6 → None（HEAD 正确渲染无 else） | [(0,or),(6,and)]（else 漂移） |
| `a and not (b and c)` | @0 → None；@6 → [(6,and),(10,or)]（正确） | [(0,and),(6,and),(10,or)]（**误融合**） |

即 v161 的门改动使走查越过 HEAD 的断链点，把 NOTTAIL 也吞进单一链；
任何门级/守卫收窄都无法同时满足两案（`not a or b` 与融合功效案拓扑
同构）。**最终形态 = 完全回退 v161 五处插入（回到 HEAD 逐字节）+
新增 `_detect_fused_not_head_chain` 专用探测器**，仅在标准走查失败
（`len(chain) < 2`）时尝试：head FALSE 跳 B；head fall-through 起的
and-run 每成员跳同一 E（E≠B 且非同价）；run ≥2 成员；末成员
fall-through == B。命中返回 [(head,'or')] + [(m,'and')…] 并继续走既有
下游（mixed-chain unify），不命中 return None（HEAD 逐字节同路径）。
判别：功效案 run=2 命中；`not a or b` run=1 不命中；NOTTAIL 首成员后
PJIT→18≠E 使 run=1 不命中。**fix161c 终判据**：a_not_or/C161_not_or/
pv8 逐字节 SAME+EQUAL；NOTTAIL 七案（E1/E3/C1/C2/C3/pv2/pv3）逐字节
SAME+EQUAL；difflib 62/62；request 190/194；六功效案与 v161 基线产品
逐字 SAME（TEXT-DIFF vs HEAD + BYTE-EQUAL）；矩阵 19 全过；电池
TEXT-DIFF 恰 6。

**fix161c 落地与验收（最终形态，+103/−1）**：完全回退 fix161 五处走查
改动（回到 HEAD 逐字节，`git diff` 空校验通过），改为新增
`_detect_fused_not_head_chain` 专用探测 + `len(chain) < 2` 处单一注入
（命中则沿用既有下游 mixed-chain unify；不命中仍 return None，HEAD 同
路径）。逐案实证：

| 案 | 判官 | 文本对照 | 结果 |
|---|---|---|---|
| not_or（`not a or b`） | EQUAL | SAME HEAD（无 else） | 零触碰恢复 ✓ |
| nottail（`a and not (b and c)`） | EQUAL | SAME HEAD | NOTTAIL 回归消除 ✓ |
| nottail3（三成员子链） | EQUAL | SAME HEAD | ✓ |
| ggo（difflib 实形） | EQUAL | SAME HEAD | ✓ |
| fused（`not a or (b and c)`） | EQUAL | SAME v161 功效基线 | 功效保持 ✓ |

整模块：**difflib 62/62（100%）**、**request 190/194（97.94%）**。
矩阵 19/19 全过（6 功效 HEAD-TEXT-DIFF+EQUAL；12 控制 SAME+EQUAL；
b116 预存在 DIFF）。收窄前基线结果已改名 `*_prefix_baseline.txt` 留存。

**纪律偏离记录（本会话）**：子代理基础设施在本会话不可用（连
`print('ok')` 的最小任务与显式 provider/model 路由均静默崩溃，累计 7 次
失败、2 个可续接子代理）。为不使规范停滞，fix161c 的补丁编写/应用与
验证由主代理直接执行并全程留证（DESIGN_r161c.md、probe3.py 两树探针、
fix161c.py、fix161c_check_result.txt）；tasks.md/checklist.md 与提交仍按
规范由主代理维护。子代理恢复后回归「实现经子代理」纪律。

**r162 选族侦察（只读，存档 r162_recon_archive.md + D:/temp/opencode/
cl_layout/r162diag/RECON.md）**：request 余 4 差单元形态归类——urlretrieve
与 add_handler 同族（语句级 if 链尾分支嫁接/降级，各仅 1 条错边，块数
相等）；ftp_open 与 retrieve 疑似同族（语句/守卫位混合链，块数不等证据
弱）。rr-v5r162 首选 **CHAINGRAFT**（预计闭合 urlretrieve+add_handler，
收窄为两条门控；与 v161 已修域条件内部正交），备选 MIXCOND-STMT（正面
重叠 v161 域，暂缓）。r162 待 v161 收尾后按单族单轮纪律启动。

甄别不成立（嵌套 if-else：链首 FALSE 目标=外层 else ≠ 末成员 fall-through；
全 and 链：链首目标=成员出口同块；多融合 not or 链：成员目标不唯一）走查尾
既有 None 路径逐位复原（C3）；登记不发生（a_not_or 等既有形）走查逐字节
不变。判据只读 CFG 跳转目标/极性/出口等价（I.4 白名单），无 B 编号/探针名/
输入值专用分支。

## 七案最小复现（判官 v161 全 EQUAL；HEAD 产品存档 *_out.py）

| 案 | 源形 | HEAD（v160） | v161 |
|---|---|---|---|
| a_not_or | `if not a or b:` | 正确（SAME 控制） | EQUAL |
| b_not_or_and | `if not a or (b and c):` | factored 反转 | EQUAL |
| c_not_or_notand | `if not host or (not port and host in names):` | factored 反转 | EQUAL |
| d_or_and | `if a or (b and c):` | 正确（SAME 控制） | EQUAL |
| e_not_a_and_b | `if a and not b:` | 正确（SAME 控制） | EQUAL |
| f_not_or_not | `if not a or not b:` | `not (a and b)` 字节等价（SAME 控制） | EQUAL |
| g_not_and_or | `if not (a and b or c):` | 正确（SAME 控制） | EQUAL |

## 验收

> 状态：fix161b/c 外科收窄前的中期读数已落盘；difflib 回归与矩阵/电池待
> 收窄后复验回填。下列读数为 v161 初版（含两处过宽守卫）实测。

**五语料判官（fresh 反编译，窗口检测 v161-NOTMIX=True，冻结比较器）**

| 语料 | v160 基线 | v161 初版 | 判定 |
|---|---|---|---|
| urllib.request | 189/194 | **190/194（97.94%）** | ✓ open_local_file 闭合，余 4 单元（urlretrieve/add_handler/ftp_open/retrieve）维持 |
| tarfile | 146/160 | 146/160（91.25%） | ✓ 失败 14 单元逐行一致 |
| cookiejar | 91/105 | 91/105（86.67%） | ✓ 失败 14 单元逐行一致 |
| subprocess | 68/78 | 68/78（87.18%） | ✓ 失败 10 单元逐行一致 |
| difflib | 62/62 | **61/62（98.39%）** | ✗ BLOCKER：get_grouped_opcodes NOTTAIL 回归（fix161c 修复后须回 62/62） |

**pytest 冻结基线（7 文件套件，G5_RERUN 历史正式口径）**：**2 failed /
282 passed / 2 xpassed** ✓ 与冻结基线完全一致（失败恰 B01_simple_if_then_
else_merge / BOUNDARY_02_large_function）。全量 `pytest tests` 的 22 nook
收集错误为结构性已知陷阱（tests/nook/* 导入缺失 batch12/batch13/async_tests/
bytecode_comparator），非反编译缺陷，不作冻结读数（备注件存档）。

**矩阵 19 案（初版）**：6 功效案全 HEAD-TEXT-DIFF + JUDGE-EQUAL ✓；12 控制
案 11 SAME+JUDGE-EQUAL ✓、b116 SAME+预存在 DIFF ✓；**C161_not_or
HEAD-TEXT-DIFF（else 风格漂移）✗**（fix161b 收窄后须 SAME）。

**电池 / 矩阵复验 / difflib 复核**：待 fix161b+c 落地后回填（判据：矩阵 19
案全过、电池 TEXT-DIFF 恰 6 功效案全 BYTE-EQUAL、E148 三案归位、R110
168/167、REG-10 维持、NO-SRC 0、difflib 62/62、request 190/194）。

## 余差（本轮不闭，登记）

（待验收后回填）

## 文件

- fix161.py / fix_patch_v5r161.diff（工作树补丁存档）
- 七案 *_src.py / *.pyc / *_out.py（HEAD 产品）/ *_v161.py（v161 产品）
- olf_dis.txt（open_local_file 反汇编侦察）
- matrix_v5r161.py / matrix_v5r161_result.txt（r161matrix）
- r161_regress.py / r161_regress_result.txt
- request_judge_v161.txt / request_judge_v160_baseline.txt /
  tarfile_judge_v161.txt / cookiejar_judge_v161.txt /
  subprocess_judge_v161.txt / difflib_judge_v161.txt / pytest_v161.txt
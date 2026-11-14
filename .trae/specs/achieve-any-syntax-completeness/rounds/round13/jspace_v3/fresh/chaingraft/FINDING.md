# rr-v5r162 CHAINGRAFT —— 语句级 if 链尾分支嫁接/降级（urllib.request 192/194 目标）

轮次：rr-v5r162（Task 88）｜域：CHAINGRAFT｜单族单轮

## 一、目标单元（request 余 4 差单元中同族的两个）

| 单元 | 现状 | 结构 |
|---|---|---|
| `urlretrieve` | 判官 Different control flow（块数 35/35 相等，唯一错边 A09/B09） | `with` 作用域内：`if url_type == "file" and not filename: return ...` 后接 `if filename: ... else: ...` —— 后续 if 被误挂成守卫 if 的 **elif**，且守卫第二成员被塞成嵌套 if |
| `OpenerDirector.add_handler` | 同上（块数 31/31，错边 A23/B23） | 循环内 4 路 `elif` 链 + `else: continue` —— **最后一个 elif 被降级进 else**，`continue` 并入 else（语义破坏：`condition=='request'` 时也 continue，跳过 `kind = kind + 1`） |

## 二、最小复现（已实证，脱离大模块可独立触发）

| 案 | 形 | 现状 |
|---|---|---|
| `cg5_elif_continue` | 循环内 4 路 elif + `else: continue` | 尾 elif 降级进 else，continue 被吞并 ✗ |
| `cg7_with_guard_then_ifelse` | `with` 内 `if A and not B: return` + `if C: ... else: ...` | 后续 if 误挂 elif、守卫成员嵌套 ✗ |
| `cg8_with_guard_then_if` | 同上但后续 if 无 else | 同样误挂 elif ✗ |
| `cg9_try_guard_then_ifelse` | 普通 `try/except` 包裹同一形 | **正确**（不复现）→ 缺陷限于 `with`/异常表作用域 |
| `cg1_guard_then_ifelse` | 无 `with` 同形 | 正确（不复现） |
| `cg4_real_add_handler` / `cg6_control_plain_elif` | 无 `continue` 的 elif 链 | 正确（对照，不得漂移） |

## 三、cg7 根因（探针 probe_cg7.py 实证，BUILD_ELIF 决策序列）

```
BUILD_ELIF block=@154 then=[158] else=[192] merge=@220   -> None      # 内层 if/else
BUILD_ELIF block=@122 then=[126,128] else=[] merge=@154  -> None      # 守卫第二成员
BUILD_ELIF block=@68  then=[122,126,128] else=[154,158,192,220,222] merge=None -> IfRegion
```

守卫 if（@68）的 else 目标 @154 同时是 **then 分支（@122）的后继/死目标**——即 @154
是整条守卫链的**短路口合并点**，不是本 if 的 else 分支。elif 构建器只看「else 目标
是否为条件块」就判 elif，未排除「该目标同时可从 then 到达」。

修复方向（fix162b）：在 `_build_elif_region` 调用前加甄别——else 目标块本身是条件
跳转块（elif 候选）且可从 then_blocks 任一块直接到达 ⇒ 清空 else_blocks、merge 指向
该块，渲染为无 else 的 if，后续 if 自成一区。I.4 白名单：块后继集合 + 末指令 opcode。

## 四、cg5 根因与修复（r162a，已落地 +48/−1）

**根因（line-trace 取证）**：`_check_elif_chain(h=76)` 一级返回 None，卡在 `_d2`
判据（`inner_merge != merge_` 且非终态）。尾 elif 条件块 94 的 false 边→112
（纯 `JUMP_BACKWARD → 6`，即 `continue`），NCPD(then=106, false=112) 沿回边给出
`inner_merge = 6`（**循环头**）≠ `merge_ = 114` ⇒ 整级弃权 → elif 被降级进 else、
`continue` 被并入 else。

**门控（[v162-CHAINGRAFT]，纯插入 47 行，新行 26013–26059）**：
① `inner_merge` 是该 elif 所在循环的 loop_header（且在 `_find_enclosing_loop(...).blocks`）；
② `inner_else_succ` 末指令 ∈ {JUMP_BACKWARD, JUMP_BACKWARD_NO_INTERRUPT} 且
`argval == inner_merge`，除该跳转外无可语句化指令（⇒ 它是 continue，不可能承载
「嵌套 if 后尾随语句」）；③ then 边入口末指令为 JUMP_FORWARD/JUMP_ABSOLUTE 且
`argval == merge_`（then 臂越过 continue 块 = elif 形态判别式）。命中则
`inner_merge := merge_`（then/false 都止于 merge_），final_else 恰为 [continue 块]，
不新建区域/AST 节点；任一不成立 ⇒ 逐字节保持原行为。

**读数**：cg5 → 4 个 elif + `else: continue`，判官 EQUAL 2/2；cg4/cg6 产物 SHA256
与改前逐字节同；cg1/2/3/7/8/9 产物逐字节同；request **190→191/194（98.45%）**
（diff 仅 add_handler：`elif condition == 'request'` 归位、continue 回 else）；
difflib 62/62（产物逐字节同）。

**已知相邻形态（预存在，另立一单）**：`else: kind = 9; continue`（false 块携带
语句）仍被降级为 `if … else: kind = 9; continue; continue`——因判据②要求「纯回边
块」。证据 D:/temp/opencode/cl_layout/r162/probe162_after.py。

## 四之二、cg7 根因与修复（r162b，已落地）

门控：else 目标是条件跳转块 ∧ 可从 then_blocks 任一块直接到达 ⇒ 清空
`else_blocks`、`merge = else_succ`（渲染为无 else 的 if，后续 if 自成一区）。

**命中实证**（临时插桩后还原，dbg162.py）：cg7 `block=@68 then=[122,126,128]
else=[154,…] esucc=@154 reach=[122]`；cg8 `@68 esucc=@114 reach=[82]`；
cg5 三次调用 `reach=[]`（正常 elif 链，else 目标不从 then 可达）⇒ 精确区分，
不误伤 elif 链。

**读数**：`numstat=74/0`、标记 2 处、py_compile OK（+74 与 r162a 备份逐行
diff 为 added 27/removed 0；git 报 48/1 与 74/0 的差异是 xdiff indent-heuristic
对齐差异，净行数一致；r162a 修复确认未回退）。cg7/cg8 判官各 2/2 = 100%
（改前 1/2，Failure: Different control flow）；cg1/cg2/cg3/cg9 与改前逐字节
相同；cg4/cg6 与 r162a 产物逐字节相同；cg5 与 r162a 产物逐字节相同。
**request 191→192/194（98.97%）**：urlretrieve 闭合，余 `FTPHandler.ftp_open`
+ `URLopener.retrieve` 两单元（MIXCOND-STMT 候选，下一轮）；difflib 62/62、
tarfile 146/160、cookiejar 91/105、subprocess 68/78 全部维持。

**工具注意**：fix162b.py 原第 70 行断言 `==1` 有 bug（应用后必为 2，且在
写入前触发 ⇒ 原脚本必然空跑失败）；已修正为 `==2`，`run_fix162b.py` 为其
可用包装（原样复用 ANCHOR/GUARD 文本）。

## 五、验收判据

矩阵 19 案 ALL PASS；电池 TEXT-DIFF 恰 6（六功效案 BYTE-EQUAL）；R110 168/167；
REG-10 维持；NO-SRC 0；pytest 2F/282P/2XP（`PYTHONUTF8=1`）；request **192/194**
（两单元闭合）；tarfile 146/160、cookiejar 91/105、subprocess 68/78、difflib
62/62 全部维持。

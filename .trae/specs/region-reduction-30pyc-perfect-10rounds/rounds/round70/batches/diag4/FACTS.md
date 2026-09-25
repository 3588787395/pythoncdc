# Round 70 · diag4 · FACTS（边跑边写）

工作区 `D:/Temp/opencode/r70gate/diag4`；仓库只读。臂名前缀 `r70diag4`。
镜像/产物根：`D:/Temp/opencode/r70gate/center`（h62.py ROOT，与各批共享，靠臂名隔离）。

## Step 0 · baseline replay

命令（2026-09-25，cwd=diag4）：
```
python -X utf8 h62.py run --arm=landed --list=targets.txt --out=dump/landed.jsonl
python -X utf8 h62.py run --arm=landed --list=canary.txt --out=dump/landed_canary.jsonl
python -X utf8 sstrict67.py build_landed targets.txt dump/strict_landed.json
```

### 官方尺（h62 run --arm=landed，targets）
| pyc | matched/total | mism 明细 [name, orig, decomp, jumpdiff, truediff] |
|---|---|---|
| order_api.pyc | **32/34** | future_order 101→92 (jd2,td36)；option_order 83→73 (jd3,td39) |
| risk_calculation/__init__.pyc | **33/35** | _on_publish_after_trading_end 486→481 (jd3,td33)；_save_testds_to_csv 71→70 (jd7,td11) |
| fileio_utils.pyc | **12/14** | acquire 96→93 (jd3,td52)；write 637→636 (jd0,td38) |

product sha：order_api `5e59c43ab22b72f1`、__init__ `22cf995ee11b1b19`、fileio `4fddfd476a09f7e6`。
与 targets.md 表头 32/34、33/35、12/14 **逐字段相同**。

### 严格尺（sstrict67 build_landed targets）
```
order_api.pyc   strict 33/36 missing=0 extra=0
   base_order        [target_diff] #136 POP_JUMP_IF_TRUE 终点 orig=('order_obj','LOAD_FAST') decomp=(<常量 '生成订单，订单号:{order_id}…'>)
   future_order      [seq_len] orig=101 decomp=93
   option_order      [seq_len] orig=83 decomp=74
__init__.pyc    strict 34/37 missing=0 extra=0
   _on_publish_after_trading_end [seq_len] orig=488 decomp=481
   _on_set_positions             [seq_len] orig=297 decomp=298
   _save_testds_to_csv           [seq_len] orig=75  decomp=72
fileio_utils.pyc strict 13/15 missing=0 extra=0
   write    [seq_len] orig=637 decomp=636
   acquire  [seq_len] orig=98  decomp=93
STRICT TOTAL ok=80 / functions=88 / defects=8
```
与 targets.md 的「严格缺陷明细」**逐字段相同**（33/36、34/37、13/15，缺陷数 3/3/2）。

> 两把尺的 orig 计数不同（官方 pbv 比较的是另一套归一化）：official `__init__` 缺的是
> publish + save_testds（无 `_on_set_positions`），official `acquire` 96→93 vs strict 98→93。
> **官方全清 = official mism 清零；严格全清另行判断。**

### 金丝雀 4 支 sha（--arm=landed）
| pyc | matched/total | sha |
|---|---|---|
| fly/data/quotation.pyc | 143/143 | `4d41187e356544e0` ✓ |
| fly/common/market_time.pyc | 10/10 | `af77224b34b203c4` ✓ |
| IQCommon/util/datetime_func.pyc | 26/26 | `e711b8ea86d49a15` ✓ |
| IQData/utils/datetime_func.pyc | 25/25 | `9d09af09249da177` ✓ |

4 支 sha 与采纳合同**完全一致**。

### 电池
- `closeout69.py battery landed` 首次调用失败：`PermissionError` on
  `center/dump/repro65_landed.jsonl` —— 另一诊断代理正在同一文件上跑 battery
  （共享 GATE dump 命名）。⇒ 改用自己的脚本 + 自己的 dump 路径（见 Step 4）。
- 本目录没有 `closeout67.py`（BRIEF Step0 写的 45 项电池命令不可用）；45 项清单 =
  round63_b*+round63_fix*+round64..67_* + PINNED(shapes_r63)（从 r69gate/center/closeout67.py
  的 repro_list 逻辑复刻），82 项 = 再加 round68_*+round69_*。见「对 BRIEF 的更正」。

## Step 1 · 归一化 hunk 表（nested_diff.py，按 code-object 全路径配对）

### fileio_utils.pyc（15 code objects，2 处真差异；无伪影）
| code object | orig | decomp | hunks | 真缺陷/伪影 |
|---|---|---|---|---|
| /FileLock#9/acquire#7 | 114 | 108 | 3 | 真：insert@48（decomp 多出 JUMP_FORWARD+time.sleep(8 条)）、delete@87（orig 的 time.sleep 12 条不在同位）、delete@107（orig 的 EXTENDED_ARG+JUMP_BACKWARD） |
| /FileIO#11/write#6 | 720 | 719 | 2 | 真：replace orig[679:681]=LOAD_CONST False+RETURN_VALUE → decomp JUMP_FORWARD（@2908）；replace orig[692]=LOAD_CONST None → decomp LOAD_CONST False（@2932/2934） |

align.py write：唯一结构差在 **orig@2908 `LOAD_CONST False; RETURN_VALUE`，decomp@2908 `JUMP_FORWARD to 2932`**；
其余 4 个 hunk 全是跳转目标偏移漂移（POP_JUMP 目标 2926→2924、3048→3046）。

### risk_calculation/__init__.pyc（43 code objects，3 处）
| code object | orig | decomp | hunks |
|---|---|---|---|
| _on_set_positions#9 | 336 | 337 | 2（EXTENDED_ARG+JUMP_BACKWARD 从 idx256 移到 idx301，JUMP_FORWARD 顶位；位移族） |
| _on_publish_after_trading_end#10 | 531 | 523 | 2（delete NOP@482；orig[491:499]=JUMP_FORWARD+time.sleep(0.01) 6 条 → decomp 1 条 NOP ⇒ **整条 `time.sleep(0.01)` 语句丢失**） |
| _save_testds_to_csv#28 | 81 | 79 | 4（insert NOP；JUMP_BACKWARD→JUMP_FORWARD；orig 有两处 `LOAD_CONST None; RETURN_VALUE`、decomp 只有一处） |

### order_api.pyc（37 code objects，2 处）
| code object | orig | decomp | hunks |
|---|---|---|---|
| /future_order#39 | 115 | 107 | 5（strategy_log.info(...) 块与后续语句**顺序错位**） |
| /option_order#40 | 94 | 85 | 6（同族：日志调用与后续语句错位 + 多条 PRECALL/CALL 丢失） |

## Step 2 · 根因（先 fileio，两支都实测）

### fileio `write`（Δ-1 官方/严格）
实测（`exp_write_ret2.py`，编译两种缩进形状）：
```
return False 在 with 之内(缩进12)：  216 POP_TOP → 218 LOAD_CONST False → 220 RETURN → 2912 PUSH_EXC_INFO
return False 在 with 之外(缩进8) ：  216 POP_TOP → 218 JUMP_FORWARD to 242 → ... PUSH_EXC_INFO
```
**orig 是「在 with 之内」布局，product 是「在 with 之外」布局 ⇒ 唯一成因：decompiler 把
`return False` 从 with 体**内部**抬到了 with 之后（product L366 与 L279 的 `with` 同为 12 缩进）。**
语义也随之错：orig 在 `__exit__` 吞掉异常时 `return None`，product `return False`。

region 实测（regdump write）：`WithRegion@4 blocks=[4,96,122,178,208,230,2912,2920,2934] children=[]`；
`return False` 所在的 block 2886/2908 只出现在 **TryExceptRegion@4.blocks** 里 ⇒ with 体边界没有把
2886/2908 圈进去，被当成 try 体的同层后继兄弟。

### fileio `acquire`（Δ-3 官方 / Δ-5 严格）
region 实测（regdump acquire）：
```
LoopRegion@42   children=[TryExceptRegion@44]
TryExceptRegion@44  children=[TryExceptRegion@304, IfRegion@108, IfRegion@152]
IfRegion@152  blocks=[152,214,532,582] then_blocks=[214] else_blocks=[532,582]
TryExceptRegion@304 blocks=[302,304,356,374,490,494,496,592,600,602]  ← parent 是外层 OSError try
```
**if@152 的 then 臂在 214 处被截断**：本应吞进的 `try: os.unlink / except BaseException / raise
FileLockException`（block 302..502）被建成了**外层 try 的兄弟子区域**，于是发射顺序变成
「if/else → try → raise」，而 orig 是「if(含 try+raise) / else(sleep)」。
根因层级：analyzer 构造 IfRegion@152 时 then 臂走不进已属 TryExceptRegion@304 的块。


## Step 2 补全 · fileio \write\ 根因（实测定案）

### 字节码事实（orig pyc，\write\ 尾部）
\BLK 2740 strategy_log.error(f'...写入报错...') (line 421)
BLK 2802  LOAD_CONST None x3 / PRECALL 2 / CALL 2 / POP_TOP   <- 内联 __exit__（line 330 = with 行）
BLK 2824  LOAD_CONST / RETURN_VALUE                            <- except 分支 return
BLK 2828  strategy_log.error('%s文件不支持写入' % self.file_name) (line 423)  exc {2828,2886}->2912 d1
BLK 2886  LOAD_CONST None x3 / PRECALL / CALL / POP_TOP        <- 内联 __exit__（exc {2886,2908}->2938 d0）
BLK 2908  LOAD_CONST False / RETURN_VALUE                      <- **line 424 的 return False（with 体内）**
BLK 2912  PUSH_EXC_INFO / WITH_EXCEPT_START                    <- with 的 handler
\异常表在 with 体内是**多段 depth1 -> 2912**（96..206 / 234..332 / 360..484 / … / 2828..2886），
段与段之间夹着 depth0 的**内联 __exit__ + return** 组（208..228 / 334..356 / … / 2886..2908）。
即 CPython 3.11 对 **with 体内每个 return** 都先内联发一段 \__exit__(None,None,None)\（该段归到 with 行），
再发 \LOAD_CONST; RETURN_VALUE\。

### 根因链（同一层次身份，无启发）
1. \_find_with_exc_entry\ 只返回**覆盖 STORE 偏移的那一条**异常表条目 => {96,208}。
2. \_extend_with_body_end\ 先按「e_start>=body_start 且 e_end>max_end 且 (e_target==exc_target or e_start<exc_target)」
   把 max_end 一路扩到 2886，再因 \exc_target(2912) > max_end\ 置 \max_end = exc_target = 2912\。
3. **收缩循环（11619-11640）把它打回 208**：扫描 \[initial_end, exc_target)\ 内第一个
   \_is_with_exit_cleanup(block) or WITH_EXCEPT_START\ 的块就 \max_end = min(max_end, block.start_offset); break\。
   实测 \_is_with_exit_cleanup(BLK208) == True\（BLK208 = LOAD_CONST None x3 + PRECALL + CALL + POP_TOP），
   且它没有更深的嵌套异常表条目 => 不走 \has_nested: continue\ => **max_end = 208**。
   （已验证：\_get_with_body_range -> (96, 208)\，EXTEND 96,208 -> 208。）
4. 于是 \WithRegion.body_offset_end = 208\，\_collect_with_body_blocks(96,208)\ 只拿到 [96,122,178]，
   R84 再补 208(当 cleanup)+230 => \locks=[4,96,122,178,208,230,2912,2920,2934]\。
   \IfRegion@96\ 的 else_blocks 止于 2828，**2886/2908 落在 try 的同层兄弟** => eturn False\ 被抬到 with 之后（缩进 12）。
5. 反编译产物 vs orig（重新编译后）：orig 908: LOAD_CONST False; RETURN_VALUE\（紧跟 handler 2912）；
   decomp 886 尾部 JUMP_FORWARD -> 2932: LOAD_CONST False; RETURN_VALUE\（跳过 handler）。
   => nested_diff \/FileIO#11/write#6\ 720->719 的两个 hunk 全部由此产生。

### 判据（三要素）
- **识别条件**：\_is_with_exit_cleanup\ 块存在某个后继 \s\，\ody_start <= s.start_offset < exc_target\（同层：
  仍在本层异常表条目 target==exc_target 的保护范围之内）。
- **归约方式**：该块是 with 体内 return 之前的**内联 __exit__**，不是 with 的正常收尾 => \continue\，继续向后扩展 body_end。
- **AST 映射**：body_end 延伸覆盖其后的 return 块 => 该 return 仍作为 \WithRegion.with_blocks\ 内的语句发射，
  不被抬到 with 之后。反向（无同层后继 => 正常收尾 => 收缩）保持原行为。

## Step 3 · 候选 r70diag4c1（spec: spec_r70diag4_c1.json，mirr: center/mirr_r70diag4c1）
锚点唯一（\max_end = min(max_end, block.start_offset)\ 全文件仅 11639 行一处）。
命令：\h62.py build --spec=... --dst=r70diag4c1\ 然后 \h62.py run --arm=r70diag4c1 ...
| 尺 | landed（基线） | r70diag4c1 |
|---|---|---|
| 官方 fileio_utils | 12/14（acquire 96->93、write 637->636） | **13/14（仅剩 acquire）** |
| 官方 order_api | 32/34 | 32/34（不变） |
| 官方 \_\_init\_\_ | 33/35 | 33/35（不变） |
| 严格 fileio_utils | 13/15（write、acquire） | **14/15（仅剩 acquire）** |
| 严格合计 | ok=80 / defects=8 | ok=81 / defects=7 |
| 金丝雀 4 sha | 4d41187e / af77224b / e711b8ea / 9d09af09 | **全部逐位相同** |

产物核对：\center/build_r70diag4c1/...fileio_utilsOK.py\ line366 eturn False\ 已回到**缩进 16（with 体内）**。
\sstrict67.py build_r70diag4c1 targets.txt dump/strict_r70diag4c1.json\ 为严格尺读数来源。
注意：\sstrict67.py <build_dir>\ 的第一个参数是 \center/build_<dir>\，跑候选必须用 \uild_r70diag4c1\；
用 \uild_landed\ 会用 REPO 的 pycdc 重跑 landed（无害但不是候选读数）。

## Step 4 · 合成见证（进行中）
\synth/r70diag4_wret.pyc\、\synth/r70diag4_wret2.pyc\（wA/wB/wC/wD 四形状）**均未复现**：
landed 与 c1 都 2/2、5/5 全清。已排除的形状：with 体内 if/elif/else 链 + 链末 eturn False\。
landed 对这些形状把 eturn False\ 吸进**最后一个 else 分支**（与 orig 同字节码，故不判差异），
而 \write\ 里 landed 是把它甩到 **with 之外（缩进 12）**。
egdump\ 对比：
- wA：\IfRegion@40 else_blocks=[...,206,250,272]\（把内联 __exit__ 250 和 return 272 都吸进 else）
- write：\IfRegion@96 else_blocks=[...,2802,2824,2828]\（**不含 2886/2908**）=> 二者被甩到 try 层
=> 见证还需要一个「让 IfRegion 不吸收尾部 __exit__+return」的形状差异（未定）。


## Step 4 · 合成见证（已咬合）

\synth/r70diag4_witness.py\ -> \.pyc\（列表 \synth_witness.txt\），单函数 \wret\：
\\python
def wret(path, kind):
    try:
        with open(path, 'w', encoding='utf-8') as fw:
            if kind == 'a':
                fw.write('a')
                return True
            fw.write('tail')
            return False
    except BaseException:
        return False
\| arm | 结果 |
|---|---|
| landed | **1/2** — wret 62 -> 61 |
| r70diag4c1 | **2/2** |

发射对照（同 pyc）：
- landed: \w.write('tail')\ / eturn False\ 被抬到 **with 之外**（缩进 8 = try 层）
- c1: 同两条语句在 **with 体内**（缩进 12）
- landed egdump\: \TryExceptRegion@4.try_blocks\ 含 168(=fw.write tail) 与 return 组，
  \WithRegion@4 blocks=[4,40,54,98,120,194,202,216]\ 圈不住尾部 => 与 \write\ 同构。

**排除的形状（landed 与 c1 都全清、故不能作见证）**：\synth/r70diag4_wret.pyc\(2/2)、
70diag4_wret2.pyc\ wA/wB/wC/wD(5/5)、70diag4_wret3.pyc\ 中 wE/wG/wH。
决定性差异：**with 体末尾的 eturn\ 前面必须是「body 层语句」且 if 链带一个把
尾部内联 __exit__+return 吸进 else 的形状时（wA）不复现；不带 else、尾部语句在 body 层时（wF）复现。**

## Step 5 · 采纳合同读数（r70diag4c1）
- 锚点出现次数：\max_end = min(max_end, block.start_offset)\ 全 egion_analyzer.py\ **1 处**（h62 build 断言过）。
- 45 项 / 82 项电池（\att70.py landed r70diag4c1\，82 项为 45 项超集）：
  **WORSE-THAN-BASE on 0 repro(s)**；两列逐格相同（含 r63_b2 7/9、r65_trytail 8/9、
  r65_diag2/fs2 6/10、r67_ccprefix2 2/3、r67_site2 4/8、r68_big_sinkreturn 1/3、
  r68b3_headif 4/7、r69d4_orchain 2/6 等所有已知欠清项均不回退）。
- 金丝雀 4 sha 逐位不变（见 Step 3 表）。
- ADR-1 seq_len 族两支判据（\write\，orig=637）：
  - 严格尺 decomp 636 -> **637**（Σ|Δ| 1 -> 0，净减），且**发射数上升**（不满足「少发射」禁区）；
  - 官方尺 637->636 的 mismatch 消失（worse=0 之外的净增）。
- 合成见证咬合：landed 1/2 / c1 2/2（见 Step 4）。

### dump 路径（本批，全部在 diag4 下，未碰 center/dump/repro65_*）
\dump/r70diag4c1_targets.jsonl\、\dump/r70diag4c1_canary.jsonl\、
\dump/strict_r70diag4c1.json\、\dump/batt_{landed,r70diag4c1}_82.jsonl\、
\dump/battlist_82.txt\、\dump/witness_{landed,r70diag4c1}.jsonl\。

### 对 BRIEF 的更正（补充）
- \closeout67.py\ 不在本目录；45/82 项电池已由自建 \att70.py\ 覆盖
  （45 = round63_b*+round63_fix*+round64..67_*+PINNED(shapes_r63)；82 = 再加 round68_*+round69_*）。
- \sstrict67.py\ 第一参数是 \center/build_<dir>\：候选必须先
  \h62.py run --arm=<cand>\（产物落 \center/build_<cand>\），再 \sstrict67.py build_<cand> ...\。


---

# 正式候选 r70diag4c3 —— fileio 官方尺 100% 全清（14/14 / 严格尺 15/15）

spec: \spec_r70diag4_c3.json\（3 处编辑，全部作用于 \core/cfg/region_analyzer.py\；
h62 build 断言每条 anchor 在原文件恰好出现 **1** 次；mirror \center/mirr_r70diag4c3\，
产物 \center/build_r70diag4c3\）。

## 三条规则（识别条件 / 归约方式 / AST 映射，均只读同层次结构身份）

**① c1 —— with 体尾部 return 归位（原 r70diag4c1）**
- 识别：\_is_with_exit_cleanup\ 块后存在同层后继 \s\（\ody_start <= s.start_offset < exc_target\，
  仍在本层异常表 target 保护范围内）。
- 归约：\continue\ 不收缩，继续向后扩展 body_end。
- 映射：body_end 覆盖其后的 return 块；return 仍作为 with 体内语句发射。

**② c2 —— while-true 循环出口候选剔除（\_find_loop_else\）**
- 识别：WHILE 且 \condition_block is None\（while-true，无条件假值驱动的 else 入口），
  候选循环出口 \S ∈ loop_successors\ 但 \S\ 可由「循环体真身」(body_set 去 header)
  沿前向边、不经 header 抵达 ⇒ \S\ 在循环代码之内，只是该路径以 raise/return 收尾、进不了自然回边。
- 归约：从 \loop_successors\ 取消该 \S\ 的出口认领；全部取消时按既有「无循环出口」路径
  eturn (None, None)\；不新增、不删除其他块。
- 映射：\S\ 及其后继归其所在嵌套区域发射；LoopRegion 不再产出 else 子句，
  也不再把 \S\ 注入 \oundary_stop\。
- 实测：\_find_loop_else(header=42, cond=None, body=[42,44,88,106,108,152,532,582,608])
  -> else=[214,302,304,354,502,592], natural_exit=214\（214 是 except 内 if 的 then 臂，
  因自然循环体 = 回边反向可达集而被漏收）→ c2 后 else=[]。

**③ c4' —— R102 子区域 break 目标同层判据（line ~6486）**
- 识别：R102 有界 DFS 候选 \_cur\ 以无条件前向跳转指向 \_cur_jt\，\_cur_jt ∉ body_set  但 \lock_to_region[_cur_jt].entry ∈ body_set\ ⇒ \_cur_jt\ 仍由「循环体内起始的区域」
  （嵌套 try 的 try 体/handler）持有，在循环之内，不是循环外 break 落点。
- 归约：不把 \_cur\ 认作 break；不新增、不删除其他块。
- 映射：\_cur\/\_cur_jt\ 归其所属嵌套区域与嵌套 if 的臂发射；LoopRegion 不吸纳 \_cur\，
  \oundary_stop\ 不再把 \_cur_jt\ 当循环出口。
- 实测：landed/c2 均 \reak_blocks=[84,354]\（354 = 内层 try 体正常出口
  \JUMP_FORWARD→502\，被误判 break → \LoopRegion.blocks\ 吸纳 354 → boundary 含 502 →
  \IfRegion@152.then_blocks=[214]\ 截断）；c3 后 break_blocks=[84]，
  \IfRegion@152.then_blocks=[214,302,304,354,502]\。

## 读数（Step 3/5 全项）

### 官方尺（h62 run）
| pyc | landed | r70diag4c3 |
|---|---|---|
| fileio_utils | 12/14（acquire 96→93、write 637→636） | **14/14  []** |
| order_api | 32/34 | 32/34（不回退） |
| risk_calculation/__init__ | 33/35 | 33/35（不回退） |

### 严格尺（sstrict67）
| pyc | landed | r70diag4c3 |
|---|---|---|
| fileio_utils | 13/15（write、acquire） | **15/15  bad=[]** |
| order_api | 33/36 | 33/36 |
| __init__ | 34/37 | 34/37 |
| STRICT TOTAL | ok=80 / defects=8 | **ok=82 / defects=6** |

### 采纳合同
- 锚点：3 编辑，每条 anchor 在 egion_analyzer.py\ 出现次数 **1/1/1**（mk_spec_c3.py 打印）。
- 45 项电池：\att70.py landed r70diag4c3 --set=45\ → **WORSE-THAN-BASE on 0**，两列逐格相同。
- 82 项电池：\att70.py landed r70diag4c3\ → **WORSE-THAN-BASE on 0**，两列逐格相同。
- 金丝雀 4 项 sha 与 matched/total 与 landed **逐字段 SAME**
  （4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177）。
- 合成见证 \synth/r70diag4_witness.pyc\：landed **1/2**（wret 62→61）→ c3 **2/2**。
- 产物语义对照：landed 把 \w.write('tail')\ / eturn False\ 抬到 with 之外（缩进 8），
  c3 在 with 体内（缩进 12）。

### 本批 dump（均在 diag4/dump 下，未触碰 center/dump/repro65_*）
70diag4c3_targets.jsonl\、70diag4c3_canary.jsonl\、\strict_r70diag4c3.json\、
\witness_r70diag4c3.jsonl\、\att_landed_{45,82}.jsonl\、\att_r70diag4c3_{45,82}.jsonl\。

### 新增探针
\probe_loopelse.py\（LoopRegion.else_blocks 赋值栈）、\probe_findelse.py\（_find_loop_else 入出参 + CFG 边）、
\probe_collect_arm.py\（_collect_branch_blocks 入出参）、egdump_arm.py\（指定镜像跑仓库分析器）、
\	race_add.py\（逐行定位 break_blocks_set.add 的落值）、\mk_spec_c3.py\（合并 spec 生成）。


---

## Step 4 · 候选与 A/B

**候选名：
70diag4c3**（正式 spec 落在 \specs/cand_r70diag4_c3.json\，同内容
\spec_r70diag4_c3.json\；3 条编辑全在 \core/cfg/region_analyzer.py\，anchor count==1/1/1）。

判据三要素见上节（① with 体尾 return 归位、② while-true 循环出口剔除、③ R102 子区域 break 目标
同层判据）；三条均只读同层次结构身份字段，无跨层包含、无函数名/偏移/阈值启发、无新增 self 状态。

\h62.py ab --a=dump/landed.jsonl --b=dump/r70diag4c3_targets.jsonl→ IMPROVED fileio_utils.pyc 12/14 -> 14/14
→ **TALLY SAME=2 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0 (unpaired=0)**；files fully matched: a=0 b=1。

五列读数（Step 4 合同项）：

| 闸门 | 命令 | landed | r70diag4c3 |
|---|---|---|---|
| targets（官方尺） | \h62.py run --list=targets.txt\ | 12+32+33 / 14+34+35 | **14+32+33 / 14+34+35** |
| battery 45 | \att70.py landed r70diag4c3 --set=45\ | 45 支基线 | **worse=0，逐格相同** |
| battery 82 | \att70.py landed r70diag4c3\ | 82 支基线 | **worse=0，逐格相同** |
| canary 4 | \h62.py run --list=canary.txt\ | 143/143,10/10,26/26,25/25 + 4 sha | **sha 与读数逐字段 SAME** |
| strict | \sstrict67.py build_r70diag4c3 targets.txt\ | 80/88, defects=8 | **82/88, defects=6；fileio 15/15** |
| synth 见证 | \h62.py run --list=synth_witness.txt\ | **1/2**（wret 62→61） | **2/2** |

ADR-1 判据（本支属缺失/过冲族 \seq_len\）：
- fileio Σ|orig−decomp|：landed \write |637−636|=1\ + \cquire |98−93|=5\ = **6** → c3 **0**（净减 6）；
- **非少发射**：decomp 条数 636→637、93→96/98（严格尺 fileio 15/15 全等）⇒ 是「补回语句」不是「丢语句」；
- 严格尺未新增 \	arget_diff\（fileio bad=[]；\order_api.base_order\ 的 #136 target_diff 与 landed 同条，非新增）；
- 纯位移族判据不适用（本支无 counts 相等的 seq_diff/target_diff 形状）。

其他合同项：ERR=0、无不反编译、锚点 count==1、未跑 402 全量。

---

## VERDICTS

- **fileio_utils.pyc → 候选：
70diag4c3**
  官方尺 **14/14 全清**（12/14 → 14/14），严格尺 **15/15 全清**（13/15 → 15/15，STRICT TOTAL 80→82）；
  ADR-1 缺失族 Σ|Δ| 6→0 且 decomp 条数上升；金丝雀 4 sha 不变；45/82 电池 worse=0；
  自建合成见证 landed 1/2 → c3 2/2（with 尾 \w.write('tail')\/eturn False\ 归回 with 体内）。
  ⇒ 满足「至少一支官方尺 100% 全清」的 mandate。

- **risk_calculation/__init__.pyc → 候选：NONE**
  landed 33/35、c3 33/35（无回退亦无改善）。剩余 3 处全为 \seq_len  （\_on_publish_after_trading_end\ 488→481、\_on_set_positions\ 297→298、\_save_testds_to_csv\ 75→72）；
  本轮未为这三处找到「只读同层次身份 + 三要素」的归约点，按纪律不硬写启发式规则。

- **order_api.pyc → 候选：NONE**
  landed 32/34、c3 32/34。剩余 3 处：\ase_order\ #136 POP_JUMP_IF_TRUE 终点 target_diff、
  \uture_order\ seq_len 101→93、\option_order\ seq_len 83→74，跨 egion_ast_generator\ 与
  \comprehension_generator\，本轮未定位到合格判据。

- **合成见证（硬规则前置）**：\synth/r70diag4_witness.py|.pyc\（函数 \wret\）已在 spec 之前产出并咬合。

---

## 对 BRIEF 的更正

1. **BRIEF 是 R69 模板**：文中工作区 \D:/Temp/opencode/r69gate/<batch>\、臂前缀 69\、spec 命名
   \specs/cand_r69_<名>.json\。本批实际为 **\D:/Temp/opencode/r70gate/diag4\**，臂前缀 **70diag4\**，
   spec 落 \specs/cand_r70diag4_c3.json\。
2. **本目录没有 \closeout67.py\**（Step 0 与 §5 引用它）⇒ 电池改用
   \python -X utf8 batt70.py <base> <arm> [--set=45|82]\（82 项 = round63..69 全集，45 为其子集，
   脚本行 5 \--set=45|82\ 可选）。
3. **\sstrict67.py\ 的第一个参数是产物目录 \center/build_<arm>\**，不是臂名；
   BRIEF 写的 \sstrict67.py <臂名> <名单>\ 会找不到产物。
4. **臂名空间共享**：本批一律用 70diag4*\ 前缀；且共享的 \center/dump/repro65_<arm>.jsonl   会与并发代理互相 resume 跳过 ⇒ 全部自建 \diag4/dump/*\ 脚本路径。
5. **\h62.py run --out=<已存在>\ 的 resume 语义**：重建镜像后必须先删旧 jsonl 再跑，
   否则读数是上一版镜像的（本批已踩一次，读数与镜像不符）。
6. **spec anchor 的坑（本轮实测）**：anchor 若只覆盖 \if\ 链前几行，repl 插入完整 \elif\ 链后，
   原链剩余分支会变成**无 guard 的孤儿 \elif\** 继续执行（c4' 第一版因此把 354 仍加进
   \reak_blocks_set\）。anchor 必须覆盖整条分支链。
7. §4「轮初基线」是 10 支 partial 官方尺 / 45 项电池的中心口径；本批 \	argets.txt\ 只含
   3 支靶 +4 支金丝雀，读数以 Step 0 实测为准（已逐字段复放并一致）。

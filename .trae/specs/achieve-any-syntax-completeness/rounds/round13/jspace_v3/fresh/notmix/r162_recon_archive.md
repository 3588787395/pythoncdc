# RECON rr-v5r162 — 4 失败单元形态归类（只读侦察）

素材：dis_*.txt / cfg_*.txt / src_*.txt（前任产出，已核验）+ **request_v161.py**（D:/temp/opencode/cl_layout/r161diag/judge/，v161 渲染源码，本次新引入为决定性证据）。
判定口径：cfgdiag 的块图等价（is_control_flow_equivalent）；orig=A*，rendered=B*。

---

## 1. 形态归类

### urlretrieve — 主因：顺序双 if 被误熔为 if/elif 链（语句级，非异常表）
源结构是两条**顺序 if**：`if url_type=='file' and not filename: return …`（早退守卫）+ `if filename: tfp=open… else: NamedTemporaryFile…`。
证据：
- dis 158/162：`==` 的 `POP_JUMP_FORWARD_IF_FALSE→254` 与 `filename` 的 `POP_JUMP_FORWARD_IF_TRUE→45(=254)` —— 守卫的两个分支**同落 254**，即下一条 if 的入口（这是"不得熔链"的形态标志）。
- v161 渲染（request_v161.py:195-203）产出 `if url_type=='file': if not filename: return …; **elif** filename: tfp=open…` —— 第二条 if 被并成 elif，url_type=='file' 且 filename 给出时 tfp 不再赋值（结构性错）。
- cfg 唯一 MISMATCH A09/B09：A 的 true_jump→A12[78]（`if filename` 测试头），B 的 true_jump→B15[122]（with tfp 入口）——真分支被嫁接越过 `tfp=open` 块。
- 块数 35/35 相等，仅此 1 条错边；两个 with（BEFORE_WITH@104/@402，异常表 10 条目）在 orig/rendered 完全对齐，**非主因**。
- 族归属一句话：与 add_handler 同族（if 链尾分支嫁接）；与 ftp_open/retrieve 不同层。

### add_handler — 主因：4 路 elif 链的尾 elif 被降级进 else（continue 吞并）
源结构：for 循环内 `if startswith('error') / elif 'open' / elif 'response' / elif 'request' / else: continue`。
证据：
- dis 508/540/572：三级 `POP_JUMP_FORWARD_IF_FALSE` 依次 →530/562/594；572 的 false→594 `JUMP_BACKWARD 130`（continue），true 落 596 共享出口——尾 elif 的假分支就是循环 continue。
- v161 渲染（request_v161.py:371-375）产出 `else: if condition=='request': …; continue` —— 尾 elif 被塞进 else，continue 落在赋值之后，condition=='request' 时会跳过 setdefault/insort（语义错）。
- cfg 唯一 MISMATCH A23/B23：A 的 natural→A24（setdefault 块），B 的 natural→B00（JUMP_BACKWARD 回 for 头）。
- 块数 31/31 相等，仅此 1 条错边；try int(kind)/except ValueError pass（异常表 3 条目，390 CHECK_EXC_MATCH）对齐无恙，**非主因**。
- 族归属一句话：与 urlretrieve 同族（链尾分支误嫁接/降级），形态不孤立。

### ftp_open — 主因：语句级 and/or 混合链 `file and 'I' or 'D'` 嫁接进 for 头
证据：
- dis 686-696：`LOAD_FAST file / POP_JUMP_FORWARD_IF_FALSE→694 / 'I' / JUMP_IF_TRUE_OR_POP→696 / 'D' / STORE_FAST type`，紧接 698 `LOAD_FAST attrs` 700 GET_ITER 702 FOR_ITER——混合链尾部与 for 头直接相邻。
- v161 渲染（request_v161.py:1120-1121）：`type = file and 'I' or 'D'` 之后错成 `for attr in file and 'I' or 'D':` —— 混合链表达式被复制为 for 可迭代。
- cfg：blocks orig=47 rendered=50（for 头被拆成 3 个多余块）；块数不等故 cfgdiag 未打印逐边 mismatch。
- 两段 try/except（OSError→URLError @324；all_errors→URLError from exp @1094，RAISE_VARARGS 2）在渲染侧全部正确，**非主因**。
- 族归属一句话：与 retrieve 的守卫条件疑似同族（and/or/not 混合链），但嫁接对象是 for 头；与 urlretrieve/add_handler 不同层。

### retrieve — 主因（疑似）：守卫 `filename is None and (not type or type=='file')` 的 not/or 混合链；双层 try/finally 为次因（未证实）
证据：
- dis 152-170：`POP_JUMP_FORWARD_IF_NOT_NONE→400` / `POP_JUMP_FORWARD_IF_FALSE→172` / `=='file'` `POP_JUMP_FORWARD_IF_FALSE→400` —— and 内嵌 (not type or type=='file') 的混合条件。
- v161 渲染（request_v161.py:1303-1315）：坍塌成 `if filename is None and type: if type=='file': pass; else: fp=self.open(url,data)` —— 守卫语义反转、错插 else、open_local_file 段被移位重复 open。
- 异常表 9 条目：[174..366)→368（except OSError pass）+ 双层 finally（外层 [446..894)→1342 fp.close，内层 [896..1204)→1248 tfp.close，finally 清理段 [1206..1248) 亦被外层覆盖）。
- 但渲染侧双层 finally 本身已正确产出（v161.py:1329-1353：try/finally tfp.close 内嵌 try/finally fp.close）——所以 finally 结构不是当前失分点的主嫌疑。
- cfg：blocks 45/47 不等，无逐边 mismatch 列表。
- 族归属一句话：与 ftp_open 同族疑似（混合链守卫），叠加未证实的 EXCNEST 因素；形态最复杂。

---

## 2. 族间比较

| 配对 | 关系 |
|---|---|
| urlretrieve ↔ add_handler | **同族**：if 链尾分支的嫁接/降级（各恰好 1 条错边，块数相等） |
| ftp_open ↔ retrieve | **疑似同族**：and/or/not 混合链出现在语句/守卫位置（retrieve 证据不完整） |
| 跨族（链尾嫁接 vs 混合链） | 不同层：前者是语句级分支-目标分配，后者是表达式级条件渲染 |

- 最大公共根因族：**CHAINGRAFT（链尾嫁接）**，覆盖 urlretrieve + add_handler，且两单元各仅 1 条错边——修复面最窄、判定增量最可预测。
- 最孤立单元：retrieve（45/47 块差 + 双层 finally + 守卫混合链叠加，无法单一定因）。
- ftp_open 居中：混合链族，但 v161 刚在该族落过一子（open_local_file 的 not/混合链融合）。

---

## 3. 选族建议（rr-v5r162，单族单轮）

### 首选：CHAINGRAFT（if 链尾分支嫁接/降级）
- 预计闭合：**urlretrieve + add_handler**（2 单元）。
- 为什么现在可行：
  - v161 已把条件内部（not/混合链融合）修好——两单元的条件表达式在渲染侧均已正确编译（urlretrieve 的 `and not filename`、add_handler 的四级测试均逐指令对齐），残余错位**全部集中在语句级链尾的边分配**。
  - 两单元各仅 1 条 mismatch 边、orig/rendered 块数相等，规则可收窄为两条门控：(a) 守卫 if 的某分支目标 == 下一条 if 的入口时，不得把后者并成 elif（urlretrieve）；(b) 尾 elif 的 false 分支 == 循环 continue（JUMP_BACKWARD 指向 FOR_ITER 邻域）时，尾 elif 不得降级进 else（add_handler）。
- 风险：
  - v148 NOTTAIL/NOTAND 形同在条件链附近，若实现时触碰条件尾分支的通用分配逻辑可能回波；
  - 全库大量 `if X: continue` / 早退守卫后接 if 的形状——必须按上述窄门控落地，勿改成通用"链合并禁用"，否则已过单元（含 v161 刚修的 open_local_file）可能回退。

### 备选：MIXCOND-STMT（and/or/not 混合链在语句/守卫位置的渲染）
- 预计闭合：**ftp_open + retrieve**（若 retrieve 主因确为守卫混合链）。
- 为什么可行：v161 的混合链修复已落在表达式内部管线，扩展两形态是同一管线的自然延伸——(a) `X and 'I' or 'D'` 语句尾紧接 for 头时，混合链结果只入 STORE，不得参与 for 可迭代（ftp_open）；(b) 守卫 `and(not or ==)` 的分支目标表（retrieve 152-170）。
- 风险：**正面重叠 v161 已修域**（open_local_file 同族刚落地，回归面直接相邻）；retrieve 的双层 finally 因素未排除，存在"修了守卫仍不过"的空转风险；ftp_open/retrieve 块数不等、缺逐边证据，规则收窄依据弱于首选。

---

## 4. 证据不足声明

- **ftp_open、retrieve**：orig/rendered 块数不等（47/50、45/47），cfgdiag 只在块数相等时打印逐边 mismatch，无法给出确切错边清单。缺：块数均衡化（或放宽 rank 映射）后的逐边 diff。
- **retrieve**：无法排除"双层 try/finally 才是主因"——缺一份"守卫单独修正后重判"的数据（本侦察不许跑反编译器，故只标注）。
- urlretrieve / add_handler 证据充分（块数相等 + 唯一 mismatch 边 + 渲染源码可复现该结构），可放心作为首选族靶。

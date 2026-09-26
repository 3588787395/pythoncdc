# R71 · fix3（修复工程师，P2/P3 族 F-EXCTABLE + F-ASSERT）BRIEF

## 0. 使命

你是 Round 71 的第三位修复工程师。repo（`F:/Downloads/pythoncdc-main`）**只读**，
工作区：`D:/Temp/opencode/r71gate/fix3`（仪器已就位，`DIAG1_FACTS.md` 是测试工程师根因事实书）。
基线 HEAD = R70 落地 `b21c5c61`；h62 `--arm=landed` = repo 字节。

按 diag1 实测（证据最硬的两族，见 `DIAG1_FACTS.md` §3.2 / §3.4）：

**族 1 = F-EXCTABLE（2 单元：`IQEngine/plugins/plugin_fly_data/fly_api/base.pyc::SplitOrder.parse_time_info`、
`IQData/entry.pyc::IQDataEntry.get_instance`）** —— 指令流 144/144 全同、**异常表不同**：
1. `TryExceptRegion.has_else=True`、`else_blocks=[114,118,148,150]`，但 `_generate_try` 返回
   `keys=['body','handlers','type'] n_orelse=0`，**else 语句已被塞进 body**（`bodylen=2`）；
2. `_generate_try_body`（def `core/cfg/region_ast_generator.py:24173`，调用点 **`:26152`**）
   返回时**把 else 块也标成已生成**（探针 `('AFTER_BODY',114,True)` 等 4 条全 True）；
3. 于是 orelse 门 `:26587` 虽触达 2 次，但循环 `:26615-26616`（`eb in self.generated_blocks: continue`）
   **8 次全 continue**，`:26626/:26639/:26696` 从未执行；`:27010 if orelse_stmts:` 触达 1 次但
   `:27011` 未执行 → `try_ast['orelse']` 永远缺键 → 重编译后 try 体吞掉 else 指令、异常表 end 被撑大。

**族 2 = F-ASSERT（1 单元：`fly_api/base.pyc::OverNightOrder.__init__`）** —— try 内的 `assert`
被降级成 `if ...: pass` + `raise AssertionError`（`LOAD_ASSERTION_ERROR` 2→0，n 188/165）：
- 阻塞点：`core/cfg/region_analyzer.py:15259-15261`
  ```python
  succs = list(cur.successors)
  if len(succs) != 1:
      return False
  ```
  **未排除「指向 handler 入口的异常边」**（block 382 succ=[384,448]，csucc=[384]，448 是
  `PUSH_EXC_INFO` handler 入口）→ try 内必然 False → `_identify_assert_regions(def :14708)`
  不产 AssertRegion → 条件块退化成普通 IfRegion（`ra-gen:11711/:17691`）→ LAE 被当普通 raise 重建。
- 同型守卫另有 `_find_assertion_error_block` `:15303-15305`（返回 None）、
  `_reaches_block_via_fallthrough` `:15310` 起。
- 负对照已钉死：synth/t15（try 外）`AssertRegion×2 reach=True` vs synth/t24（try 内）
  `AssertRegion=0 reach=False`，唯一差别是 handler 边 448。t24 已实测 status=failure。

## 1. 步骤

1. 读 `DIAG1_FACTS.md` §3.2/§3.4；读 `D:/Temp/opencode/r71gate/diag1/synth/`（t09/t10/t13/t24/t25 等
   与 try 相关的复现，逐支确认 failure 类别）。
2. 复现与探针：对两族靶 pyc 跑 `python -X utf8 F:/Downloads/pythoncdc-main/scripts/pyc_verify.py single
   <pyc> --source <OK.py>`；monkeypatch 打印 `_generate_try_body`/orelse 门/`_identify_assert_regions`。
   **region_analyzer 无模块级 `import dis`，探针用 dis 必须局部导入**（R67 陷阱：NameError 被宽
   except 吞掉、产物静默退化）。
3. 写候选 spec（每族一份，或合一份均可）：`{"file": "core/cfg/<x>.py", "edits":[{"anchor":...,"repl":...}]}`
   **repl 内嵌三要素注释（识别条件/归约方式/AST 映射），标签 `[R71-exctable]` / `[R71-assert]`**；
   同层次结构身份判据：无函数名/文件名/偏移常量/阈值启发、无名字白名单、无新增 self 状态、
   无跨层 `region.entry in r.blocks` 型模式。
   注意 F-ASSERT 是**收紧/放宽既有守卫的结构条件**（排除异常边），必须只影响「该 successor 是
   异常表 handler 入口」的情形，不得把普通双后继条件块误判成 assert。
4. 验证闭环 a–e（同 fix1 规格）：
   a. `python -X utf8 mbuild71.py <臂> specs/<候选>.json`（锚点断言全过）；
   b. 靶支官方读数逐项不变或改善 + mandated `pyc_verify.py single` 失败单元清零或减少且零新增；
   c. 金丝雀：`market_time` sha `af77224b34b203c4`、两支 `datetime_func` `e711b8ea86d49a15`/
      `9d09af09249da177`、`quotation` `4d41187e356544e0` 与 R70 逐字节相同（h62 sha 口径），
      quotation 官方 143/143 维持；
   d. `python -X utf8 closeout69.py battery landed <臂>` worse-than-landed=0；
   e. `python -X utf8 sstrict67.py build_<臂> <靶清单> dump/strict_<臂>.json` 无新增缺陷函数。
5. 合成咬合：编译最小复现（try+else、try+assert 两形状），在臂上反编译并 `pyc_verify single` 确认转绿；
   负对照形状（无 else 的 try、try 外 assert）读数不变。

## 2. 硬约束

- **不修改 repo 任何文件**；禁止 402 全量扫描；每条命令 <300s；land71 只可 dry-run。
- h62 list LF 无 BOM、跑前删旧 jsonl；PowerShell 重定向是 UTF-16，一律 python 侧写文件；
  绝对 pyc 路径。
- ADR-1：任何他支回归即整件拒收；缺陷族 Σ|Δ| 不得上升。
- F-EXCTABLE 属「指令全同、仅异常表」族：验收看 mandated 尺 failure 消失 + 官方读数不回退 +
  严格尺缺陷集不新增。

## 3. 交付

- `specs/<候选>.json`（每族一份 + anchor 自检输出）
- `FACTS.md`：根因复核、三要素判据、a–e 读数、金丝雀 sha、合成咬合、候选/拒绝清单
- `synth/*.py` 最小复现
- 最终回复：候选清单 → 文件/编辑处数 → a–e 结论 → 靶支读数 → 是否建议中心采纳。

不要 git commit/push（中心统一做）。逐步可验证，禁止投机取巧。

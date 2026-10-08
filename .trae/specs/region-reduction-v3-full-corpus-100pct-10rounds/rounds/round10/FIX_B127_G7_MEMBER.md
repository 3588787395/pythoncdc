# Round 10 工单 #15（B127）落地回报 —— G7 尾块身份改「区域成员事实」

标记：`[r10-b127-g7member]`
工作副本：`D:/Temp/r15b/wt`（镜像；**仓库 core/ 未被编辑**，交付物为补丁 `D:/Temp/r15b/b127.patch`）
判据：`scripts/pyc_verify.py`（compare-only），产物一律 `python -X utf8 pycdc.py <in.pyc> -o <out>` 重生成，先删旧产物。

## 0. 环境/镜像自证

- [x] 镜像 `core/ bytecode/ parsers/ utils/ scripts/ pycdc.py` 逐文件 sha256 与仓库一致（`verify_failures=0`，35 个 pyc + 35 个既有产物全部一致）
- [x] 镜像 HEAD 态跑 `pycdc.py handlers.pyc` 得到的产物与仓库现有 `handlersOK.py` **逐字节相同**（sha256 前16位 `65badb9485d3b8f3`）⇒ 镜像执行的就是 HEAD 的 `core`
- [x] `core/cfg/region_ast_generator.py` HEAD sha256 `e9a8f65f6451bcc895c5558528b03a9d6ef1045f418f0efd267f9900ef174e74`

## 1. 复现票面仪器（HEAD 态，镜像产物）

仪器：`D:/Temp/r15b/b127_hunk.py`（r10loss 同款 + §六 要求的嵌套 code object 归一 `<co qualname>` + root 参数化）。

```
IQCommon/logger/handlers.pyc :: <module>.TWHThreadController._target      len 199/197 hunks=17  contentdiff=1
IQCommon/logger/handlers.pyc :: <module>.TWHThreadRotatingFileHandler._target len 126/126 hunks=0 contentdiff=0
```
⇒ 票面 §一「17 hunks / 唯一内容差 delete orig[75:77]=LOAD_CONST None|RETURN_VALUE」与 §二.3 负对照 **均已按现字节复现**。

`pyc_verify single`（HEAD 态、镜像产物）：`status=failure units=29/30`，失败单元 =
`<module>.TWHThreadController._target: Failure: Different control flow`。

## 2. 站点复验（票面锚点 vs 实测）

- [x] `:51806-51812` G7 代码分支、`POP_TOP` 巧合支、`:51813-51821` `_joint_owner`、`:51700` docstring (G7) 段：**锚点全部在位，行号与票面一致**。
- [ ] 票面 §三「本案是 B121 落点集里 G7 放行/抑制的取舍」——实测：见 §3。

## 3. 实测所有权事实（探针 `D:/Temp/r15b/probe_b127.py`、普查 `D:/Temp/r15b/survey.py`）

（待填）

## 4. 判据实现

（待填）

## 5. 验收读数

- [ ] 17→0
- [ ] single 30/30
- [ ] 负对照 Equal
- [ ] quotation 153/153
- [ ] anchor 454/454
- [ ] small34 1528/1568

## 6. 名单单元 2–7

（待填）

## 7. 结论

（待填）

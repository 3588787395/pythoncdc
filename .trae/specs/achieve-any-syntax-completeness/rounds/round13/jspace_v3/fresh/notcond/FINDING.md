# rr-v5r159 [v159-NOTCOND] not 复合条件 if 语义反转族——FALSE 模式 BoolOp 链准入窗扩展
# （REAL46-016 urllib.request 187→188/194）

## 功效案（urllib.request.HTTPRedirectHandler.redirect_request 实形，源 line 664-666）

```python
m = req.get_method()
if (not (code in (301, 302, 303, 307, 308) and m in ("GET", "HEAD")
         or code in (301, 302, 303) and m == "POST")):
    raise HTTPError(req.full_url, code, msg, headers, fp)
```

v158 渲染 `if code in (301,...,308): if not (m in (...) or code in (...) and
m == 'POST'): raise`——not(A∧B∨C∧D) 被重组为嵌套 factored 形=真实 R1（**语义
反转**：¬A 时源码 raise、渲染不 raise——如 305 redirect 会漏检；判官
Different bytecode：ORIG A 假边→60 下一 or 成员，REC A 假边→128 跳过 raise）。

## 根因

`_detect_boolop_conditional_chain` 的入口块 body 语句判据 `_sb_has_body` 扫描
「条件起始之后」的指令（`_cond_start_offset` 门控）。POP_JUMP_IF_FALSE（and
短路模式）分支的栈深回溯准入窗只放行「简单变量真值测试」（LOAD_*/LOAD_ATTR/
LOAD_METHOD 结尾）与 R54-A 混合链结构判据——`x in T` 成员测试形（CONTAINS_OP
+ POP_JUMP_IF_FALSE）不在窗内 → 前置赋值（`m = req.get_method()` 的 STORE）
被 `_sb_has_body` 当 if 体 → BoolOp 链在首操作数块拒绝启动 → or 链碎片化
（区域树探针实证：d 案 BoolOpRegion blocks=[58,66] 仅 C∧D、A 独立
IfRegion[0,50]=factored 外层；e 案（无前置赋值）BoolOpRegion blocks=[0,10,18,26]
整链）→ 渲染语义反转。对照组实证链走查本身对 or-run 结构完备（无前置赋值形
faithful）——缺口仅在入口块前置语句的豁免准入窗。TRUE 模式（R38）准入窗早已
含 IS_OP/CONTAINS_OP/COMPARE_OP（`value is DEFAULT or callable(value)` 实形）
——本修复把同一理据镜像到 FALSE 模式的 CONTAINS_OP。

## 修复（只增不破，单文件 +14/−1，[v159-NOTCOND] 一处标记）

`core/cfg/region_analyzer.py` `_detect_boolop_conditional_chain` 的
POP_JUMP_IF_FALSE 分支准入窗追加 `'CONTAINS_OP'`（与 R38 的 TRUE 窗同一成员
测试理据）：命中即放行既有栈深回溯体——回溯后 `_cond_start_offset`=条件首
操作数入栈点，前置语句不再被 `_sb_has_body` 当 body，BoolOp 链在首操作数块
正常启动（整链归约 faithful 渲染）。IS_OP/COMPARE_OP 仍排除（COMPARE_OP 链
式比较/boolop 结果比较回归风险——既有注释；IS_OP 无语料证据，登记后续）。
不命中逐字节落回现状（C3）。

## 验收

- rr（全形）/d_precall 复现案判官 Equal/Equal（HEAD 渲染 factored 形
  Different bytecode → v159 渲染 faithful 形全 Equal）
- urllib.request **187→188/194（96.91%）** redirect_request 闭合，余 6 单元
  全 Different control flow 维持
- tarfile 146/160、cookiejar 91/105、subprocess 68/78 登记基线全维持；
  difflib 判官 62/62=100.00% 维持
- 矩阵 15 案 ALL PASS（E1 rr/E3 not_mixed/E4 not_single/E5 two_preassign/
  E6 precall_shape 共 5 功效案全 HEAD-TEXT-DIFF→v159 JUDGE-EQUAL 字节验证；
  E2 preassign_and 同形案 SAME+JUDGE-EQUAL=and 链嵌套形与扁平形重编译字节等
  同、HEAD 已正确=修复精确性实证；C1 无前置赋形/C2 TRUE 模式 R38 既有窗/
  C4 简单变量窗/C5 kwmerge/C6 delwin/C7 retfin/C8 binparen 全 SAME+JUDGE-
  EQUAL=既有域零触碰；C3 compare/C9 B116 SAME 预存在 DIFF 维持）
- 电池 425 案（R110 169 + V111..V122/V148..V158 累计 + V159 15）——五文件交换；TEXT-DIFF 5/425=E159 五功效案登记改进案（全 BYTE-EQUAL），E158/E157/E156 十六案归位（TEXT-SAME BYTE-EQUAL），R110 169 案 TEXT 一致 168/签名一致 167 与 r147..r158 基线逐位一致、REG-10 其余 9 案 SAME-SIGNATURE 含 SUBST-SIG pd8_prod、na5=r144 登记改进 A/B 口径归一、NO-SRC 0
- pytest 2F/282P/2XP 冻结基线（B01/BOUNDARY_02）

## 余差（本轮不闭，登记）

- urllib.request 余 6 差单元（全 Different control flow）：urlretrieve/
  OpenerDirector.add_handler/HTTPPasswordMgr.find_user_password/
  FileHandler.open_local_file（diff=2 单跳合并差，已定向）/FTPHandler.ftp_open/
  URLopener.retrieve——控制流差定向 sweep 专项轮
- FALSE 窗 IS_OP（`x is D and ...` 前置赋值形）无语料证据登记后续；
  COMPARE_OP 链式比较/boolop 结果比较域维持排除
- tarfile 余 14 差单元（itn 链式比较专项轮 / _load D1 域专项轮已登记）；
  REAL46-013 cookiejar 91/105、015 subprocess 68/78 余差；4 compile_error；
  pytest 余 2 冻结对（登记态）；REG-10 名单缩减（na5 移出）

## 文件

- matrix_v5r159.py / matrix_v5r159_result.txt（r159matrix）
- r159_regress.py / r159_regress_result.txt
- request_judge_v159.txt（188/194 终态）/ request_judge_v158_baseline.txt /
  tarfile_judge_v159.txt / cookiejar_judge_v159.txt / subprocess_judge_v159.txt /
  difflib_judge_v159.txt
- rr_src.py / rr.pyc / rr_out.py（HEAD 渲染）/ rr_out2.py（v159 渲染）/
  rr_rec.pyc / d_precall_src.py
- fix159.py / fix_patch_v5r159.diff

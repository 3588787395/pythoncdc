# rr-v5r160 [v160-DEEPRET] 深层循环内 return 的 N 对帧清理前瞻族
# （REAL46-016 urllib.request 188→189/194）

## 功效案（urllib.request.HTTPPasswordMgr.find_user_password 实形，源 line 850-858）

```python
def find_user_password(self, realm, authuri):
    domains = self.passwd.get(realm, {})
    for default_port in True, False:
        reduced_authuri = self.reduce_uri(authuri, default_port)
        for uris, authinfo in domains.items():
            for uri in uris:
                if self.is_suburi(uri, reduced_authuri):
                    return authinfo        # ← v159 渲染裸 Expr `authinfo`
    return None, None
```

v159 渲染 `authinfo`（裸表达式语句）——return 关键字丢失=真实 R1（函数永不
返回 authinfo；判官 Different bytecode：ORIG [LOAD authinfo, (SWAP, POP_TOP)×3,
RETURN_VALUE] vs REC [LOAD authinfo, POP_TOP, ...]）。

## 根因

CPython 3.11 对 k 层循环内的 `return X` 发射 <eval X> + (SWAP(2)+POP_TOP)×k +
RETURN_VALUE——每对 SWAP+POP_TOP 弹一层循环迭代器帧，返回值驻留栈底被
RETURN_VALUE 消费（deep3 块图：B124=[LOAD, (SWAP,POP)×3, RETURN] 单块）。
主语句循环（_generate_block_statements_body）中 **SKIP_OPS 含 SWAP** → SWAP
不进语句缓冲 → POP_TOP 分支的帧清理前瞻是唯一识别点。该分支既有前瞻只认
两形：POP+RETURN（1 对后续）与 POP+SWAP+POP+RETURN（2 对后续）——k=3 形的
POP+SWAP+POP+**SWAP**+POP+RETURN 不匹配 → 首个 POP 落 Expr-flush
（`pop_expr` 重建为 Expr(authinfo)）；后续 POP 各自命中既有模式跳过 → 残留
stmts=[Expr(authinfo)]+Return(None) 形破坏 R23-N6 促销判据 → Return 值丢失。
2 层形（k=2，deep2 对照）由既有模式 2 自愈——**仅在 k≥3 触发**。

侦察过程存档：主语句循环内 RC2/RC3 SWAP 处理器（SKIP_OPS 之后的死代码路径，
SWAP 永不达）曾被误判为修复点——line-trace + 逐指令探针实证 SWAP 在循环顶部
SKIP_OPS 即被跳过（修复 v1 无效已回退）；真修复点=POP_TOP 分支前瞻。

## 修复（只增不破，单文件 +21/−0，[v160-DEEPRET] 一处标记）

`core/cfg/region_ast_generator.py` POP_TOP 分支前瞻加泛化 N 对匹配：剩余段
匹配 `SWAP + (POP_TOP + SWAP)* + POP_TOP + RETURN_VALUE`（k-1 对 SWAP+POP
交替后随 POP+RETURN）→ 跳过本 POP（帧清理，不落 Expr-flush）。既有模式 1/2
先命中逐位不变；不命中逐字节落回现状（C3）。k=2 形新路径与既有模式 2 产物
逐字相同（矩阵 C2 实证）；k≥3 形 stmt_instrs=[值] 直达 RETURN 分支 →
Return(值) 直接发射。

## 验收

- deep3（k=3 精确形）/deep2（k=2 对照）判官 Equal/Equal（HEAD 渲染裸 Expr
  Different bytecode → v160 渲染 `return authinfo` 全 Equal）
- urllib.request **188→189/194（97.42%）** find_user_password 闭合，余 5 单元
  维持（urlretrieve/add_handler/open_local_file/ftp_open/retrieve）
- tarfile 146/160、cookiejar 91/105、subprocess 68/78 登记基线全维持；
  difflib 判官 62/62=100.00% 维持
- 矩阵 14 案 ALL PASS（E1 find_user_pw/E2 deep3_min/E3 deep4(k=4)/E4
  deep3_retuple/E5 deep3_2ret 共 5 功效案全 HEAD-TEXT-DIFF→v160 JUDGE-EQUAL
  字节验证；C1 deep1/C2 deep2 既有形/C3 无循环 return/C4 循环无 return/C5
  kwmerge/C6 delwin/C7 notcond/C8 binparen 全 SAME+JUDGE-EQUAL=既有域零触碰；
  C9 B116 SAME 预存在 DIFF 维持）
- 电池 439 案（R110 169 + V111..V122/V148..V159 累计 + V160 14）——五文件交换；TEXT-DIFF 5/439=E160 五功效案登记改进案（全 BYTE-EQUAL），E159/E158/E157/E156 十七案归位（TEXT-SAME BYTE-EQUAL），R110 169 案 TEXT 一致 168/签名一致 167 与 r147..r159 基线逐位一致、REG-10 其余 9 案 SAME-SIGNATURE 含 SUBST-SIG pd8_prod、na5=r144 登记改进 A/B 口径归一、NO-SRC 0
- pytest 2F/282P/2XP 冻结基线（B01/BOUNDARY_02）

## 余差（本轮不闭，登记）

- urllib.request 余 5 差单元（全 Different control flow）：urlretrieve/
  OpenerDirector.add_handler/FileHandler.open_local_file（diff=2 单跳合并差，
  已定向=not 复合条件族 factored 形，语义反转）【注：open_local_file 与
  redirect_request 同属 not-factored 语义反转族，v159 修复未覆盖其
  `not host or (not port and ...)` 融合 not or→and 混合链形】/FTPHandler.
  ftp_open/URLopener.retrieve——控制流差定向 sweep 专项轮
- **融合 not or→and 混合链族**（`if not host or (not port and X):` 渲染
  `if host: if not port and X:`——三形复现（纯形/前导 if/try 包裹均触发）
  深度根因已存档：SKIP_OPS 后 or 链走查对融合 not 极性成员（IF_FALSE→body）
  不识别 → 链碎片化 → factored 语义反转；and 链构建器极性重建已备（`not
  port` 正确）、缺 or 链走查准入 + or→and 混合统一器方向——专项轮
- tarfile 余 14 差单元（itn 链式比较专项轮 / _load D1 域专项轮已登记）；
  REAL46-013 cookiejar 91/105、015 subprocess 68/78 余差；4 compile_error；
  pytest 余 2 冻结对（登记态）；REG-10 名单缩减（na5 移出）

## 文件

- matrix_v5r160.py / matrix_v5r160_result.txt（r160matrix）
- r160_regress.py / r160_regress_result.txt
- request_judge_v160.txt（189/194 终态）/ request_judge_v159_baseline.txt /
  tarfile_judge_v160.txt / cookiejar_judge_v160.txt / subprocess_judge_v160.txt /
  difflib_judge_v160.txt
- deep3_src.py / deep3.pyc / deep3_out.py（HEAD 渲染）/ deep3_out2.py（v160
  渲染）/ deep3_rec.pyc / deep2_src.py / deep2.pyc（k=2 对照）
- fix160.py / fix_patch_v5r160.diff

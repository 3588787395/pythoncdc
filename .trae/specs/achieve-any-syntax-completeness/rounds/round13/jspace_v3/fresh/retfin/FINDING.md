# rr-v5r158 [v158-RETFIN] try+finally 内联 return 值重组族——if 臂穿 finally 正常路径副本
# （REAL46-016 urllib.request 186→187/194）

## 功效案（urllib.request.FancyURLopener.http_error_302 实形，源 line 2152-2168）

```python
def http_error_302(self, url, fp, errcode, errmsg, headers, data=None):
    self.tries += 1
    try:
        if self.maxtries and self.tries >= self.maxtries:
            if hasattr(self, 'http_error_500'):
                meth = self.http_error_500
            else:
                meth = self.http_error_default
            return meth(url, fp, 500, 'Internal Server Error: Redirect Recursion', headers)
        result = self.redirect_internal(url, fp, errcode, errmsg, headers, data)
        return result
    finally:
        self.tries = 0
```

v157 渲染 `meth(url, fp, 500, ...)`（Expr）+ `return 0`——调用结果被丢弃、
恒返回 0（真实 R1，判官 Different bytecode：ORIG [CALL][LOAD_CONST 0;
STORE_ATTR tries][RETURN_VALUE] 中 RETURN 持有栈底 CALL 结果；REC 多出
POP_TOP + LOAD_CONST 0 = 恒 0）。

## 根因

CPython 3.11 零成本 finally 对 return-in-try 发射 <值求值> + [finally 正常
路径副本内联] + RETURN_VALUE——返回值驻留栈底穿越块界（B144 值尾块
[PUSH_NULL, LOAD meth, args, CALL] 直落 B172 副本块 [LOAD_CONST 0, LOAD_FAST
self, STORE_ATTR tries, RETURN_VALUE]，异常表 36-172→250 恰在副本块前截断）。
if 臂走查 `_process_if_blocks`（then 臂块循环）两层缺口：①值尾块经
`_generate_block_statements` 尾 flush 渲染 Expr，既有 Expr→Return 转换被
`self._try_depth <= 0` 门挡住（try 上下文恒 >0）；②后继 RETURN 块拉入路径
把 B172 当普通 return 块渲染 `return 0`（RETURN 抓副本尾常量）。B207
return-in-finally 归约不适用：其直落判定 `_fall_through` 用「末有效指令
偏移+2」——CALL 带 CACHE 尾垫使 +2≠副本块起始（164≠172），且 B207 只在
`_generate_try_body` 块循环触发（该处 if 臂块已被 if 生成提前消费——探针实证
`[BODY] block=50 gen=True`）。STORE_FAST result 名字形（B188→B234）由 B75
前置归约（`_b75_try_arm_returns`）正确重组，仅内联 CALL 值形缺（探针实证
`[B75] rets=[144]` 预登记存在但 if 臂生成不查该台账）。

## 修复（只增不破，单文件 +131/−0，[v158-RETFIN] 两处标记）

`core/cfg/region_ast_generator.py`：

1. `_process_if_blocks` 后继 RETURN 拉入站点前加精确形判定——臂末语句为
   Expr ∧ 本块有效运行无语句终结符（纯值生产运行）∧ 命中即臂末 Expr 原位
   升格 `Return(值)`（stmts[-1] is bs[-1] 同一对象），后继副本链登记
   generated（副本体由 finalbody/fc_keep 机制唯一归属发射，fc_keep=0 抑制
   不重复）。任一条件不成立逐位落回既有拉入路径（C3）。
2. 新增只读方法 `_v158_try_arm_return_in_finally(value_block, first_succ)`——
   B207 同式词汇：①值尾块纯值生产运行（无 STORE/POP_TOP/RETURN/跳转/
   RAISE/IMPORT 终结符）②直落后继=本块后继中唯一非 PUSH_EXC_INFO 块（异常
   入口排除；副本起始可跨 CALL CACHE 尾垫，B207 的 +2 判据不适用）③链逐块
   （≤8 跳）为任一区域 finally_copy_blocks 台账成员或 finally 异常副本体
   （剥噪/剥 PUSH_EXC_INFO/剥框架尾）连续 opcode 切片同构 ④链尾有效运行以
   RETURN_VALUE/RETURN_CONST 终结且 RETURN 前运行（POP_TOP 剥尾）可重建
   （副本体保守验证）。

## 验收

- retfin2 精确形复现案判官 Equal/Equal（HEAD 渲染 `meth(...); return 0`
  Different bytecode → v158 渲染 `return meth(...)` 全 Equal）
- urllib.request **186→187/194（96.39%）** http_error_302 闭合，余 7 单元
  全 Different control flow 维持
- tarfile 146/160、cookiejar 91/105、subprocess 68/78 登记基线全维持；
  difflib 判官 62/62=100.00% 维持
- 矩阵 16 案 ALL PASS（E1 http302 功效案 HEAD-TEXT-DIFF→v158 JUDGE-EQUAL
  字节验证；E2 min_call/E3 arith/E4 nested_call/E5 attr/E6 two_stmt_finally/
  E7 else_arm 同形案全 SAME+JUDGE-EQUAL=该族在 HEAD 已正确、修复精确性实证
  ——本族仅在臂尾值块被臂内嵌套 if 分块时触发；C1 try 体顶层 return（既有
  路径）/C2 名形式 B75/C3 无 finally/C4 常量 return/C5 handler_ret（v152
  HANDLERRET 域）/C6 kwmerge/C7 delwin/C8 binparen 全 SAME+JUDGE-EQUAL=
  既有域零触碰；C9 B116 SAME 预存在 DIFF 维持）
- 电池 410 案（R110 169 + V111..V122/V148..V157 累计 + V158 16）——五文件交换；TEXT-DIFF 1/410=E158_http302 登记改进案（BYTE-EQUAL），E156/E157 十五案归位（TEXT-SAME BYTE-EQUAL），R110 169 案 TEXT 一致 168/签名一致 167 与 r147..r157 基线逐位一致、REG-10 其余 9 案 SAME-SIGNATURE 含 SUBST-SIG pd8_prod、na5=r144 登记改进 A/B 口径归一、NO-SRC 0
- pytest 2F/282P/2XP 冻结基线（B01/BOUNDARY_02）

## 余差（本轮不闭，登记）

- urllib.request 余 7 差单元（全 Different control flow）：urlretrieve/
  OpenerDirector.add_handler/HTTPRedirectHandler.redirect_request/
  HTTPPasswordMgr.find_user_password/FileHandler.open_local_file/
  FTPHandler.ftp_open/URLopener.retrieve——控制流差定向 sweep 专项轮
- tarfile 余 14 差单元（itn 链式比较专项轮 / _load D1 域专项轮已登记）；
  REAL46-013 cookiejar 91/105、015 subprocess 68/78 余差；4 compile_error；
  pytest 余 2 冻结对（登记态）；REG-10 名单缩减（na5 移出）

## 文件

- matrix_v5r158.py / matrix_v5r158_result.txt（r158matrix）
- r158_regress.py / r158_regress_result.txt
- request_judge_v158.txt（187/194 终态）/ request_judge_v157_baseline.txt /
  tarfile_judge_v158.txt / cookiejar_judge_v158.txt / subprocess_judge_v158.txt /
  difflib_judge_v158.txt
- retfin2_src.py / retfin2.pyc / retfin2_out.py（HEAD 渲染）/ retfin2_out2.py
  （v158 渲染）/ retfin2_rec.pyc
- fix158.py / fix_patch_v5r158.diff

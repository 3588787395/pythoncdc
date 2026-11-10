# rr-v5r157 [v157-DELWIN] IfRegion 条件块前置语句段 DELETE 操作数窗口形 del 还原族
# （REAL46-016 urllib.request 185→186/194）

## 功效案（urllib.request.urlcleanup 实形）

```python
def urlcleanup():
    for temp_file in _url_tempfiles:
        try:
            os.unlink(temp_file)
        except OSError:
            pass
    del _url_tempfiles[:]          # ← v156 渲染整句丢失
    global _opener
    if _opener:
        _opener = None
```

v156 渲染丢 `del _url_tempfiles[:]`（判官 Different bytecode：LOAD_GLOBAL
_url_tempfiles; LOAD_CONST None; LOAD_CONST None; BUILD_SLICE; DELETE_SUBSCR
五指令蒸发，urlcleanup 37→32 指令）。

## 根因

`_if_extract_cond_instructions` 的 [v133-DELSTMT] 分支发射 del 语句时要求
`not pre_instrs`（语句边界=窗口空）。该判据对简单名形（DELETE_GLOBAL `del
re`，无操作数装载指令）成立；但 DELETE_SUBSCR/DELETE_ATTR 的操作数装载窗口
（LOAD obj / 键装载 / BUILD_SLICE）先落入默认累积——DELETE 到达时 pre_instrs
恒非空 → 分支不命中 → 窗口+DELETE 整段留在 pre_instrs；提取器循环尾部无
flush 直接返回 `(pre_stmts, cond_instrs)`，pre_instrs 弃置 = 整句蒸发。
[v133-DELSTMT] 的 DELETE_ATTR/DELETE_SUBSCR 支路在操作数窗口形下是死代码
分支。本例 B86 为双角色块（del 语句前缀 + `if _opener:` 测试尾），IfRegion
以 B86 为 condition_block，前置语句段丢失即 urlcleanup 的 del 丢失。

## 修复（只增不破，单文件 +44/−5，[v157-DELWIN] 一处标记）

`core/cfg/region_ast_generator.py` `_if_extract_cond_instructions` 的
DELETE_ATTR/DELETE_SUBSCR 分支加操作数窗口精确形：pre_instrs 非空时经
expr_reconstructor 模拟窗口装载，栈恰为 DELETE 消费数（DELETE_ATTR→1、
DELETE_SUBSCR→2；多余残留 ⇒ 非精确窗口维持旧行为）时调
`_build_delete_stmt(instr, 窗口+[DELETE])` 归约单条 Delete 发射 pre_stmts
并清空 pre_instrs。空 pre_instrs 既有 v133 路径逐位保留；非精确窗口形维持
默认累积。语言级依据：条件块内 DELETE_* 恒为完整语句终结（del 不可作子表
达式），前缀窗口自最后一次语句终结（STORE_*/POP_TOP flush）后累积，窗口外
无未终结残留——「栈恰 N 项」判据把误配封死。

## 验收

- delslice 复现案判官 Equal/Equal（HEAD 渲染丢 del 判官 Different bytecode
  → v157 渲染 `del _tmp[:]` 归位判官全 Equal）
- urllib.request **185→186/194（95.88%）** urlcleanup 闭合
- tarfile 146/160、cookiejar 91/105、subprocess 68/78 登记基线全维持；
  difflib 判官 62/62=100.00% 维持
- 矩阵 17 案 ALL PASS（E1 urlcleanup/E2 del_slice/E3 del_attr/E4 del_key/E5
  multilevel/E6 rslice/E7 multi_target/C4 after_assign 共 8 功效案全 HEAD-
  TEXT-DIFF→v157 JUDGE-EQUAL 字节验证；C1 简单名 del v133 既有/C2 循环体 del
  loop-exit 机/C3 无 if 直落/C5 kwmerge/C6 dual_unpack/C7 cfo2/C8 binparen
  全 SAME+JUDGE-EQUAL=既有域零触碰；C9 B116 SAME 预存在 DIFF 维持）
- 电池 394 案（R110 169 + V111..V122/V148..V156 累计 + V157 17）——五文件交换；TEXT-DIFF 8/394=E157 八功效案登记改进（全 BYTE-EQUAL），E156 七案归位（TEXT-SAME BYTE-EQUAL），R110 169 案 TEXT 一致 168/签名一致 167 与 r147..r156 基线逐位一致、REG-10 其余 9 案 SAME-SIGNATURE 含 SUBST-SIG pd8_prod、na5=r144 登记改进 A/B 口径归一、NO-SRC 0
- pytest 2F/282P/2XP 冻结基线（B01/BOUNDARY_02）

## 余差（本轮不闭，登记）

- urllib.request 余 8 差单元：urlretrieve/OpenerDirector.add_handler/
  HTTPRedirectHandler.redirect_request/HTTPPasswordMgr.find_user_password/
  FileHandler.open_local_file/FTPHandler.ftp_open/URLopener.retrieve（全
  Different control flow）；FancyURLopener.http_error_302（Different
  bytecode——try+finally 内 `return meth(...)` 的 3.11 内联 finally 形
  [CALL 结果][finally 语句][RETURN_VALUE] 值重组丢失：CALL 结果被当 Expr
  POP_TOP 弹掉、RETURN 抓 finally 尾 LOAD_CONST 0 → 渲染 `meth(...); return
  0`。STORE_FAST result 名字形重组正确，仅内联 CALL 值形缺；专项轮登记）
- tarfile 余 14 差单元（itn 链式比较专项轮 / _load D1 域专项轮已登记）；
  REAL46-013 cookiejar 91/105、015 subprocess 68/78 余差；4 compile_error；
  pytest 余 2 冻结对（登记态）；REG-10 名单缩减（na5 移出）

## 文件

- matrix_v5r157.py / matrix_v5r157_result.txt（r157matrix）
- r157_regress.py / r157_regress_result.txt
- request_judge_v157.txt（186/194 终态）/ tarfile_judge_v157.txt /
  cookiejar_judge_v157.txt / subprocess_judge_v157.txt / difflib_judge_v157.txt
- delslice_src.py / delslice.pyc / delslice_out.py（HEAD 渲染）/
  delslice_out2.py（v157 渲染）
- fix157.py / derive157.py（derive 内联于电池生成记录）/ fix_patch_v5r157.diff

# rr-v5r156 [v156-BINPAREN] BinOp 同优先级右子括号族（REAL46-014 tarfile 145→146/160）

## 功效案（tarfile.TarFile.close 实形）

```python
self.fileobj.write(NUL * (BLOCKSIZE * 2))   # tarfile 源 line 1966
```

v155 渲染 `NUL * BLOCKSIZE * 2`——同优先级右嵌套 BinOp 丢失括号被重结合为左结合形
（真实 R1：重编译字节序不同，`LOAD NUL; LOAD BLOCKSIZE; LOAD 2; BINARY_OP;
BINARY_OP` vs `LOAD NUL; LOAD BLOCKSIZE; BINARY_OP; LOAD 2; BINARY_OP`，判官
Different bytecode @ line 1425 offset 36）。

## 根因

code_generator.py 两条 BinOp 渲染路径（dict 路径 `_generate_binop_from_dict`、
AST 路径 `_generate_binary`）对右子表达式用同一括号判据：`right_prec ==
current_precedence and op_str in ('-', '/', '//', '%')`——同优先级右子只在
`-`,`/`,`//`,`%` 四算子时加括号。而左结合算子 `* + @ << >> & ^ |` 的右嵌套形
（源码 `a * (b * c)` 编译为 LOAD a; LOAD b; LOAD c; OP; OP，栈重建 faithful
产出右嵌套 BinOp(a, BinOp(b,c))）不加括号渲染成左结合形——重解析/重编译都改
变结合分组。`-`,`/`,`//`,`%` 既有行为正确（他们的右嵌套形同样必须括号，历史
已修）；`**` 右结合、右嵌套形不带括号重解析即原形，不需括号。

关键事实：右嵌套形与左嵌套形的字节序**永不相同**（LOAD/OP 交错序不同），所以
对全部左结合算子加括号只可能把"字节不等"修成"字节相等"，不存在"本来相等被加
括号破坏"的案型——修复零回归风险（矩阵 C1-C9 实证）。

## 修复（只增不破，单文件两处）

`core/cfg/code_generator.py`（+15/−3）：

1. `_generate_binary`（AST 路径）右子括号集 `('-', '/', '//', '%')` 扩为
   `('+', '-', '*', '@', '/', '//', '%', '<<', '>>', '&', '^', '|')`，照既有
   模式传 `current_precedence + 1` 强制子级自身收尾括号。
2. `_generate_binop_from_dict`（dict 路径，v2 重建器主路径）同一括号集同一扩法。

`'-','/','//','%'` 仍在集合中逐位不变；`**` 不入集（右结合豁免）；Compare/
BoolOp/UnaryOp 各自路径零触碰。

## 验收

- close_min 复现案判官 Equal/Equal（HEAD 渲染 `NUL * BLOCKSIZE * 2` 判官 Different
  bytecode → v156 渲染 `NUL * (BLOCKSIZE * 2)` 判官全 Equal）
- tarfile **145→146/160（91.25%）**——TarFile.close 闭合；其余 159 单元失败
  名单与失败模式逐条一致（零漂移）；cookiejar 91/105、subprocess 68/78、
  urllib.request 185/194 登记基线全维持
- difflib 判官 62/62=100.00% 维持
- 矩阵 17 案 ALL PASS（E1 close/E2 mul/E3 add/E4 cross_mul_div/E5 cross_add_sub/
  E6 shift/E7 bitwise 全 HEAD-TEXT-DIFF→v156 JUDGE-EQUAL；E8 集内豁免 `%`/`-`
  形 SAME+JUDGE-EQUAL=既有集零触碰；C1 左嵌套/C2 除法既有/C3 幂右结合/C4 低优先
  级右子/C5 括号左子/C6 kwmerge/C7 dual_unpack/C8 cfo2 全 SAME+JUDGE-EQUAL；
  C9 B116 SAME 预存在 DIFF 维持）
- 电池 378 案（R110 169 + V111..V122/V148..V155 累计 + V156 17）——五文件交换；TEXT-DIFF 7/378=E156 七功效案登记改进（全 BYTE-EQUAL），E155 两案归位（TEXT-SAME BYTE-EQUAL），R110 169 案 TEXT 一致 168/签名一致 167 与 r147..r155 基线逐位一致、REG-10 其余 9 案 SAME-SIGNATURE 含 SUBST-SIG pd8_prod、na5=r144 登记改进 A/B 口径归一、NO-SRC 0
- pytest 2F/282P/2XP 冻结基线（B01/BOUNDARY_02）
- REAL46 全量 sweep 小修口径豁免

## 余差（本轮不闭，登记）

tarfile 余 14 差单元：itn（and 链链式比较成员，走查 argval≠merge 截断 + AST 侧
操作数分组联动——专项轮已登记，fix156_andcc 已试半修回退）、_load（while-True
header 赋值吞没 + 极性反转，D1 域专项轮）、TarFile.__init__/_check/add/gettarinfo/
list/next、TarInfo.create_pax_header、_FileInFile.read、_Stream.__init__/
_init_read_gz/_read、main。

## 文件

- matrix_v5r156.py / matrix_v5r156_result.txt（r156matrix）
- r156_regress.py / r156_regress_result.txt
- tarfile_judge_v156.txt（146/160 终态）/ cookiejar_judge_v156.txt /
  subprocess_judge_v156.txt / request_judge_v156.txt / difflib_judge_v156.txt
- close_min_src.py / close_min_out.py（HEAD 渲染）/
  close_min_out2.py（v156 渲染）
- fix156.py（generator）/ fix156_battery.py / derive156.py
- fix_patch_v5r156.diff

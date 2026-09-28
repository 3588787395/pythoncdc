# R75 diag1 · `real_quote.get_tick_direction` ADR-1 解剖（dump/tick_direction75.md）

口径与 `center/adr73.py` 完全一致：pylingual `matching_iter` 对齐后按 `key_raw`（opname+argrepr）/`key_norm`（跳转参数归一为 `J`、code object 归一为 `CODEOBJ`）做 SequenceMatcher，非 equal 段计 hunk；`sdelta`=|target差| 之和；`deltas` 为跳转 argval 差异。
对照单元 `<module>.RealQuoteData.get_tick_direction`，orig_len=258。


对照臂：`landed` = 仓库 `real_quoteOK.py`；其余 = R74 `center/build_<arm>/` 产物。

## 1. 指标一览（orig_len=258，取 matched orig）

| arm | len[orig,prod] | hunks | hunks_norm | first_diff | sdelta | deltas |
|---|---|---|---|---|---|---|
| landed | [258, 259] | 12 | 2 | 4 | 184 | #4 POP_JUMP_FORWARD_IF_FALSE to 512->to 514 (+2); #139 POP_JUMP_FORWARD_IF_FALSE to 298->to 464 (+166); #235 POP_JUMP_FORWARD_IF_FALSE to 504->to 488 (-16) |
| absj | [258, 259] | 12 | 2 | 4 | 184 | #4 POP_JUMP_FORWARD_IF_FALSE to 512->to 514 (+2); #139 POP_JUMP_FORWARD_IF_FALSE to 298->to 464 (+166); #235 POP_JUMP_FORWARD_IF_FALSE to 504->to 488 (-16) |
| absj3 | [258, 259] | 12 | 2 | 4 | 184 | #4 POP_JUMP_FORWARD_IF_FALSE to 512->to 514 (+2); #139 POP_JUMP_FORWARD_IF_FALSE to 298->to 464 (+166); #235 POP_JUMP_FORWARD_IF_FALSE to 504->to 488 (-16) |
| absj9 | [258, 260] | 5 | 3 | 4 | 4 | #4 POP_JUMP_FORWARD_IF_FALSE to 512->to 516 (+4) |
| absjt | [258, 260] | 5 | 3 | 4 | 4 | #4 POP_JUMP_FORWARD_IF_FALSE to 512->to 516 (+4) |
| try7_9 | [258, 260] | 5 | 3 | 4 | 4 | #4 POP_JUMP_FORWARD_IF_FALSE to 512->to 516 (+4) |
| try7_10d | [258, 260] | 5 | 3 | 4 | 4 | #4 POP_JUMP_FORWARD_IF_FALSE to 512->to 516 (+4) |
| try7_3 | [258, 259] | 12 | 2 | 4 | 184 | #4 POP_JUMP_FORWARD_IF_FALSE to 512->to 514 (+2); #139 POP_JUMP_FORWARD_IF_FALSE to 298->to 464 (+166); #235 POP_JUMP_FORWARD_IF_FALSE to 504->to 488 (-16) |

## 2. 归一化 hunk 内容（key_norm 序列上的非 equal 段）

### arm=landed · hunks_norm=2
- **#1** `delete` orig[148:174] -> prod[148:148]
    - O  148 JUMP_FORWARD to 348                           norm=JUMP_FORWARD J
    - O  149 LOAD_FAST flag                                norm=LOAD_FAST flag
    - O  150 LOAD_CONST 1                                  norm=LOAD_CONST 1
    - O  151 COMPARE_OP ==                                 norm=COMPARE_OP ==
    - O  152 POP_JUMP_FORWARD_IF_FALSE to 322              norm=POP_JUMP_FORWARD_IF_FALSE J
    - O  153 LOAD_GLOBAL NULL + system_log                 norm=LOAD_GLOBAL NULL + system_log
    - O  154 LOAD_ATTR debug                               norm=LOAD_ATTR debug
    - O  155 LOAD_GLOBAL NULL + _                          norm=LOAD_GLOBAL NULL + _
    - O  156 LOAD_CONST "分笔数据转化异常，默认返回空值"                  norm=LOAD_CONST "分笔数据转化异常，默认返回空值"
    - O  157 CALL                                          norm=CALL
    - O  158 CALL                                          norm=CALL
    - O  159 POP_TOP                                       norm=POP_TOP
    - O  160 JUMP_FORWARD to 344                           norm=JUMP_FORWARD J
    - O  161 LOAD_FAST flag                                norm=LOAD_FAST flag
    - O  162 LOAD_CONST -1                                 norm=LOAD_CONST -1
    - O  163 COMPARE_OP ==                                 norm=COMPARE_OP ==
    - O  164 POP_JUMP_FORWARD_IF_FALSE to 344              norm=POP_JUMP_FORWARD_IF_FALSE J
    - O  165 LOAD_GLOBAL NULL + system_log                 norm=LOAD_GLOBAL NULL + system_log
    - O  166 LOAD_ATTR debug                               norm=LOAD_ATTR debug
    - O  167 LOAD_GLOBAL NULL + _                          norm=LOAD_GLOBAL NULL + _
    - O  168 LOAD_CONST "分笔数据返回空值"                         norm=LOAD_CONST "分笔数据返回空值"
    - O  169 CALL                                          norm=CALL
    - O  170 CALL                                          norm=CALL
    - O  171 POP_TOP                                       norm=POP_TOP
    - O  172 LOAD_FAST redata                              norm=LOAD_FAST redata
    - O  173 RETURN_VALUE                                  norm=RETURN_VALUE
- **#2** `insert` orig[258:258] -> prod[232:259]
    - P  232 LOAD_FAST flag                                norm=LOAD_FAST flag
    - P  233 LOAD_CONST 1                                  norm=LOAD_CONST 1
    - P  234 COMPARE_OP ==                                 norm=COMPARE_OP ==
    - P  235 POP_JUMP_FORWARD_IF_FALSE to 488              norm=POP_JUMP_FORWARD_IF_FALSE J
    - P  236 LOAD_GLOBAL NULL + system_log                 norm=LOAD_GLOBAL NULL + system_log
    - P  237 LOAD_ATTR debug                               norm=LOAD_ATTR debug
    - P  238 LOAD_GLOBAL NULL + _                          norm=LOAD_GLOBAL NULL + _
    - P  239 LOAD_CONST "分笔数据转化异常，默认返回空值"                  norm=LOAD_CONST "分笔数据转化异常，默认返回空值"
    - P  240 CALL                                          norm=CALL
    - P  241 CALL                                          norm=CALL
    - P  242 POP_TOP                                       norm=POP_TOP
    - P  243 JUMP_FORWARD to 510                           norm=JUMP_FORWARD J
    - P  244 LOAD_FAST flag                                norm=LOAD_FAST flag
    - P  245 LOAD_CONST -1                                 norm=LOAD_CONST -1
    - P  246 COMPARE_OP ==                                 norm=COMPARE_OP ==
    - P  247 POP_JUMP_FORWARD_IF_FALSE to 510              norm=POP_JUMP_FORWARD_IF_FALSE J
    - P  248 LOAD_GLOBAL NULL + system_log                 norm=LOAD_GLOBAL NULL + system_log
    - P  249 LOAD_ATTR debug                               norm=LOAD_ATTR debug
    - P  250 LOAD_GLOBAL NULL + _                          norm=LOAD_GLOBAL NULL + _
    - P  251 LOAD_CONST "分笔数据返回空值"                         norm=LOAD_CONST "分笔数据返回空值"
    - P  252 CALL                                          norm=CALL
    - P  253 CALL                                          norm=CALL
    - P  254 POP_TOP                                       norm=POP_TOP
    - P  255 LOAD_FAST redata                              norm=LOAD_FAST redata
    - P  256 RETURN_VALUE                                  norm=RETURN_VALUE
    - P  257 LOAD_CONST None                               norm=LOAD_CONST None
    - P  258 RETURN_VALUE                                  norm=RETURN_VALUE

### arm=absj · hunks_norm=2
- **#1** `delete` orig[148:174] -> prod[148:148]
    - O  148 JUMP_FORWARD to 348                           norm=JUMP_FORWARD J
    - O  149 LOAD_FAST flag                                norm=LOAD_FAST flag
    - O  150 LOAD_CONST 1                                  norm=LOAD_CONST 1
    - O  151 COMPARE_OP ==                                 norm=COMPARE_OP ==
    - O  152 POP_JUMP_FORWARD_IF_FALSE to 322              norm=POP_JUMP_FORWARD_IF_FALSE J
    - O  153 LOAD_GLOBAL NULL + system_log                 norm=LOAD_GLOBAL NULL + system_log
    - O  154 LOAD_ATTR debug                               norm=LOAD_ATTR debug
    - O  155 LOAD_GLOBAL NULL + _                          norm=LOAD_GLOBAL NULL + _
    - O  156 LOAD_CONST "分笔数据转化异常，默认返回空值"                  norm=LOAD_CONST "分笔数据转化异常，默认返回空值"
    - O  157 CALL                                          norm=CALL
    - O  158 CALL                                          norm=CALL
    - O  159 POP_TOP                                       norm=POP_TOP
    - O  160 JUMP_FORWARD to 344                           norm=JUMP_FORWARD J
    - O  161 LOAD_FAST flag                                norm=LOAD_FAST flag
    - O  162 LOAD_CONST -1                                 norm=LOAD_CONST -1
    - O  163 COMPARE_OP ==                                 norm=COMPARE_OP ==
    - O  164 POP_JUMP_FORWARD_IF_FALSE to 344              norm=POP_JUMP_FORWARD_IF_FALSE J
    - O  165 LOAD_GLOBAL NULL + system_log                 norm=LOAD_GLOBAL NULL + system_log
    - O  166 LOAD_ATTR debug                               norm=LOAD_ATTR debug
    - O  167 LOAD_GLOBAL NULL + _                          norm=LOAD_GLOBAL NULL + _
    - O  168 LOAD_CONST "分笔数据返回空值"                         norm=LOAD_CONST "分笔数据返回空值"
    - O  169 CALL                                          norm=CALL
    - O  170 CALL                                          norm=CALL
    - O  171 POP_TOP                                       norm=POP_TOP
    - O  172 LOAD_FAST redata                              norm=LOAD_FAST redata
    - O  173 RETURN_VALUE                                  norm=RETURN_VALUE
- **#2** `insert` orig[258:258] -> prod[232:259]
    - P  232 LOAD_FAST flag                                norm=LOAD_FAST flag
    - P  233 LOAD_CONST 1                                  norm=LOAD_CONST 1
    - P  234 COMPARE_OP ==                                 norm=COMPARE_OP ==
    - P  235 POP_JUMP_FORWARD_IF_FALSE to 488              norm=POP_JUMP_FORWARD_IF_FALSE J
    - P  236 LOAD_GLOBAL NULL + system_log                 norm=LOAD_GLOBAL NULL + system_log
    - P  237 LOAD_ATTR debug                               norm=LOAD_ATTR debug
    - P  238 LOAD_GLOBAL NULL + _                          norm=LOAD_GLOBAL NULL + _
    - P  239 LOAD_CONST "分笔数据转化异常，默认返回空值"                  norm=LOAD_CONST "分笔数据转化异常，默认返回空值"
    - P  240 CALL                                          norm=CALL
    - P  241 CALL                                          norm=CALL
    - P  242 POP_TOP                                       norm=POP_TOP
    - P  243 JUMP_FORWARD to 510                           norm=JUMP_FORWARD J
    - P  244 LOAD_FAST flag                                norm=LOAD_FAST flag
    - P  245 LOAD_CONST -1                                 norm=LOAD_CONST -1
    - P  246 COMPARE_OP ==                                 norm=COMPARE_OP ==
    - P  247 POP_JUMP_FORWARD_IF_FALSE to 510              norm=POP_JUMP_FORWARD_IF_FALSE J
    - P  248 LOAD_GLOBAL NULL + system_log                 norm=LOAD_GLOBAL NULL + system_log
    - P  249 LOAD_ATTR debug                               norm=LOAD_ATTR debug
    - P  250 LOAD_GLOBAL NULL + _                          norm=LOAD_GLOBAL NULL + _
    - P  251 LOAD_CONST "分笔数据返回空值"                         norm=LOAD_CONST "分笔数据返回空值"
    - P  252 CALL                                          norm=CALL
    - P  253 CALL                                          norm=CALL
    - P  254 POP_TOP                                       norm=POP_TOP
    - P  255 LOAD_FAST redata                              norm=LOAD_FAST redata
    - P  256 RETURN_VALUE                                  norm=RETURN_VALUE
    - P  257 LOAD_CONST None                               norm=LOAD_CONST None
    - P  258 RETURN_VALUE                                  norm=RETURN_VALUE

### arm=absj3 · hunks_norm=2
- **#1** `delete` orig[148:174] -> prod[148:148]
    - O  148 JUMP_FORWARD to 348                           norm=JUMP_FORWARD J
    - O  149 LOAD_FAST flag                                norm=LOAD_FAST flag
    - O  150 LOAD_CONST 1                                  norm=LOAD_CONST 1
    - O  151 COMPARE_OP ==                                 norm=COMPARE_OP ==
    - O  152 POP_JUMP_FORWARD_IF_FALSE to 322              norm=POP_JUMP_FORWARD_IF_FALSE J
    - O  153 LOAD_GLOBAL NULL + system_log                 norm=LOAD_GLOBAL NULL + system_log
    - O  154 LOAD_ATTR debug                               norm=LOAD_ATTR debug
    - O  155 LOAD_GLOBAL NULL + _                          norm=LOAD_GLOBAL NULL + _
    - O  156 LOAD_CONST "分笔数据转化异常，默认返回空值"                  norm=LOAD_CONST "分笔数据转化异常，默认返回空值"
    - O  157 CALL                                          norm=CALL
    - O  158 CALL                                          norm=CALL
    - O  159 POP_TOP                                       norm=POP_TOP
    - O  160 JUMP_FORWARD to 344                           norm=JUMP_FORWARD J
    - O  161 LOAD_FAST flag                                norm=LOAD_FAST flag
    - O  162 LOAD_CONST -1                                 norm=LOAD_CONST -1
    - O  163 COMPARE_OP ==                                 norm=COMPARE_OP ==
    - O  164 POP_JUMP_FORWARD_IF_FALSE to 344              norm=POP_JUMP_FORWARD_IF_FALSE J
    - O  165 LOAD_GLOBAL NULL + system_log                 norm=LOAD_GLOBAL NULL + system_log
    - O  166 LOAD_ATTR debug                               norm=LOAD_ATTR debug
    - O  167 LOAD_GLOBAL NULL + _                          norm=LOAD_GLOBAL NULL + _
    - O  168 LOAD_CONST "分笔数据返回空值"                         norm=LOAD_CONST "分笔数据返回空值"
    - O  169 CALL                                          norm=CALL
    - O  170 CALL                                          norm=CALL
    - O  171 POP_TOP                                       norm=POP_TOP
    - O  172 LOAD_FAST redata                              norm=LOAD_FAST redata
    - O  173 RETURN_VALUE                                  norm=RETURN_VALUE
- **#2** `insert` orig[258:258] -> prod[232:259]
    - P  232 LOAD_FAST flag                                norm=LOAD_FAST flag
    - P  233 LOAD_CONST 1                                  norm=LOAD_CONST 1
    - P  234 COMPARE_OP ==                                 norm=COMPARE_OP ==
    - P  235 POP_JUMP_FORWARD_IF_FALSE to 488              norm=POP_JUMP_FORWARD_IF_FALSE J
    - P  236 LOAD_GLOBAL NULL + system_log                 norm=LOAD_GLOBAL NULL + system_log
    - P  237 LOAD_ATTR debug                               norm=LOAD_ATTR debug
    - P  238 LOAD_GLOBAL NULL + _                          norm=LOAD_GLOBAL NULL + _
    - P  239 LOAD_CONST "分笔数据转化异常，默认返回空值"                  norm=LOAD_CONST "分笔数据转化异常，默认返回空值"
    - P  240 CALL                                          norm=CALL
    - P  241 CALL                                          norm=CALL
    - P  242 POP_TOP                                       norm=POP_TOP
    - P  243 JUMP_FORWARD to 510                           norm=JUMP_FORWARD J
    - P  244 LOAD_FAST flag                                norm=LOAD_FAST flag
    - P  245 LOAD_CONST -1                                 norm=LOAD_CONST -1
    - P  246 COMPARE_OP ==                                 norm=COMPARE_OP ==
    - P  247 POP_JUMP_FORWARD_IF_FALSE to 510              norm=POP_JUMP_FORWARD_IF_FALSE J
    - P  248 LOAD_GLOBAL NULL + system_log                 norm=LOAD_GLOBAL NULL + system_log
    - P  249 LOAD_ATTR debug                               norm=LOAD_ATTR debug
    - P  250 LOAD_GLOBAL NULL + _                          norm=LOAD_GLOBAL NULL + _
    - P  251 LOAD_CONST "分笔数据返回空值"                         norm=LOAD_CONST "分笔数据返回空值"
    - P  252 CALL                                          norm=CALL
    - P  253 CALL                                          norm=CALL
    - P  254 POP_TOP                                       norm=POP_TOP
    - P  255 LOAD_FAST redata                              norm=LOAD_FAST redata
    - P  256 RETURN_VALUE                                  norm=RETURN_VALUE
    - P  257 LOAD_CONST None                               norm=LOAD_CONST None
    - P  258 RETURN_VALUE                                  norm=RETURN_VALUE

### arm=absj9 · hunks_norm=3
- **#1** `replace` orig[231:232] -> prod[231:233]
    - O  231 JUMP_FORWARD to 512                           norm=JUMP_FORWARD J
    - P  231 LOAD_CONST None                               norm=LOAD_CONST None
    - P  232 RETURN_VALUE                                  norm=RETURN_VALUE
- **#2** `replace` orig[247:248] -> prod[248:250]
    - O  247 JUMP_FORWARD to 512                           norm=JUMP_FORWARD J
    - P  248 LOAD_CONST None                               norm=LOAD_CONST None
    - P  249 RETURN_VALUE                                  norm=RETURN_VALUE
- **#3** `replace` orig[256:257] -> prod[258:259]
    - O  256 LOAD_FAST pd_dict                             norm=LOAD_FAST pd_dict
    - P  258 LOAD_CONST None                               norm=LOAD_CONST None

### arm=absjt · hunks_norm=3
- **#1** `replace` orig[231:232] -> prod[231:233]
    - O  231 JUMP_FORWARD to 512                           norm=JUMP_FORWARD J
    - P  231 LOAD_CONST None                               norm=LOAD_CONST None
    - P  232 RETURN_VALUE                                  norm=RETURN_VALUE
- **#2** `replace` orig[247:248] -> prod[248:250]
    - O  247 JUMP_FORWARD to 512                           norm=JUMP_FORWARD J
    - P  248 LOAD_CONST None                               norm=LOAD_CONST None
    - P  249 RETURN_VALUE                                  norm=RETURN_VALUE
- **#3** `replace` orig[256:257] -> prod[258:259]
    - O  256 LOAD_FAST pd_dict                             norm=LOAD_FAST pd_dict
    - P  258 LOAD_CONST None                               norm=LOAD_CONST None

### arm=try7_9 · hunks_norm=3
- **#1** `replace` orig[231:232] -> prod[231:233]
    - O  231 JUMP_FORWARD to 512                           norm=JUMP_FORWARD J
    - P  231 LOAD_CONST None                               norm=LOAD_CONST None
    - P  232 RETURN_VALUE                                  norm=RETURN_VALUE
- **#2** `replace` orig[247:248] -> prod[248:250]
    - O  247 JUMP_FORWARD to 512                           norm=JUMP_FORWARD J
    - P  248 LOAD_CONST None                               norm=LOAD_CONST None
    - P  249 RETURN_VALUE                                  norm=RETURN_VALUE
- **#3** `replace` orig[256:257] -> prod[258:259]
    - O  256 LOAD_FAST pd_dict                             norm=LOAD_FAST pd_dict
    - P  258 LOAD_CONST None                               norm=LOAD_CONST None

### arm=try7_10d · hunks_norm=3
- **#1** `replace` orig[231:232] -> prod[231:233]
    - O  231 JUMP_FORWARD to 512                           norm=JUMP_FORWARD J
    - P  231 LOAD_CONST None                               norm=LOAD_CONST None
    - P  232 RETURN_VALUE                                  norm=RETURN_VALUE
- **#2** `replace` orig[247:248] -> prod[248:250]
    - O  247 JUMP_FORWARD to 512                           norm=JUMP_FORWARD J
    - P  248 LOAD_CONST None                               norm=LOAD_CONST None
    - P  249 RETURN_VALUE                                  norm=RETURN_VALUE
- **#3** `replace` orig[256:257] -> prod[258:259]
    - O  256 LOAD_FAST pd_dict                             norm=LOAD_FAST pd_dict
    - P  258 LOAD_CONST None                               norm=LOAD_CONST None

### arm=try7_3 · hunks_norm=2
- **#1** `delete` orig[148:174] -> prod[148:148]
    - O  148 JUMP_FORWARD to 348                           norm=JUMP_FORWARD J
    - O  149 LOAD_FAST flag                                norm=LOAD_FAST flag
    - O  150 LOAD_CONST 1                                  norm=LOAD_CONST 1
    - O  151 COMPARE_OP ==                                 norm=COMPARE_OP ==
    - O  152 POP_JUMP_FORWARD_IF_FALSE to 322              norm=POP_JUMP_FORWARD_IF_FALSE J
    - O  153 LOAD_GLOBAL NULL + system_log                 norm=LOAD_GLOBAL NULL + system_log
    - O  154 LOAD_ATTR debug                               norm=LOAD_ATTR debug
    - O  155 LOAD_GLOBAL NULL + _                          norm=LOAD_GLOBAL NULL + _
    - O  156 LOAD_CONST "分笔数据转化异常，默认返回空值"                  norm=LOAD_CONST "分笔数据转化异常，默认返回空值"
    - O  157 CALL                                          norm=CALL
    - O  158 CALL                                          norm=CALL
    - O  159 POP_TOP                                       norm=POP_TOP
    - O  160 JUMP_FORWARD to 344                           norm=JUMP_FORWARD J
    - O  161 LOAD_FAST flag                                norm=LOAD_FAST flag
    - O  162 LOAD_CONST -1                                 norm=LOAD_CONST -1
    - O  163 COMPARE_OP ==                                 norm=COMPARE_OP ==
    - O  164 POP_JUMP_FORWARD_IF_FALSE to 344              norm=POP_JUMP_FORWARD_IF_FALSE J
    - O  165 LOAD_GLOBAL NULL + system_log                 norm=LOAD_GLOBAL NULL + system_log
    - O  166 LOAD_ATTR debug                               norm=LOAD_ATTR debug
    - O  167 LOAD_GLOBAL NULL + _                          norm=LOAD_GLOBAL NULL + _
    - O  168 LOAD_CONST "分笔数据返回空值"                         norm=LOAD_CONST "分笔数据返回空值"
    - O  169 CALL                                          norm=CALL
    - O  170 CALL                                          norm=CALL
    - O  171 POP_TOP                                       norm=POP_TOP
    - O  172 LOAD_FAST redata                              norm=LOAD_FAST redata
    - O  173 RETURN_VALUE                                  norm=RETURN_VALUE
- **#2** `insert` orig[258:258] -> prod[232:259]
    - P  232 LOAD_FAST flag                                norm=LOAD_FAST flag
    - P  233 LOAD_CONST 1                                  norm=LOAD_CONST 1
    - P  234 COMPARE_OP ==                                 norm=COMPARE_OP ==
    - P  235 POP_JUMP_FORWARD_IF_FALSE to 488              norm=POP_JUMP_FORWARD_IF_FALSE J
    - P  236 LOAD_GLOBAL NULL + system_log                 norm=LOAD_GLOBAL NULL + system_log
    - P  237 LOAD_ATTR debug                               norm=LOAD_ATTR debug
    - P  238 LOAD_GLOBAL NULL + _                          norm=LOAD_GLOBAL NULL + _
    - P  239 LOAD_CONST "分笔数据转化异常，默认返回空值"                  norm=LOAD_CONST "分笔数据转化异常，默认返回空值"
    - P  240 CALL                                          norm=CALL
    - P  241 CALL                                          norm=CALL
    - P  242 POP_TOP                                       norm=POP_TOP
    - P  243 JUMP_FORWARD to 510                           norm=JUMP_FORWARD J
    - P  244 LOAD_FAST flag                                norm=LOAD_FAST flag
    - P  245 LOAD_CONST -1                                 norm=LOAD_CONST -1
    - P  246 COMPARE_OP ==                                 norm=COMPARE_OP ==
    - P  247 POP_JUMP_FORWARD_IF_FALSE to 510              norm=POP_JUMP_FORWARD_IF_FALSE J
    - P  248 LOAD_GLOBAL NULL + system_log                 norm=LOAD_GLOBAL NULL + system_log
    - P  249 LOAD_ATTR debug                               norm=LOAD_ATTR debug
    - P  250 LOAD_GLOBAL NULL + _                          norm=LOAD_GLOBAL NULL + _
    - P  251 LOAD_CONST "分笔数据返回空值"                         norm=LOAD_CONST "分笔数据返回空值"
    - P  252 CALL                                          norm=CALL
    - P  253 CALL                                          norm=CALL
    - P  254 POP_TOP                                       norm=POP_TOP
    - P  255 LOAD_FAST redata                              norm=LOAD_FAST redata
    - P  256 RETURN_VALUE                                  norm=RETURN_VALUE
    - P  257 LOAD_CONST None                               norm=LOAD_CONST None
    - P  258 RETURN_VALUE                                  norm=RETURN_VALUE

## 3. 原始 hunk（key_raw，含跳转目标数值）

### arm=landed · hunks=12
- **#1** `replace` orig[4:5] -> prod[4:5] · norm hunk 无对应 · jump-delta #4 POP_JUMP_FORWARD_IF_FALSE to 512->to 514 (+2)
    - O    4 POP_JUMP_FORWARD_IF_FALSE to 512
    - P    4 POP_JUMP_FORWARD_IF_FALSE to 514
- **#2** `replace` orig[139:140] -> prod[139:140] · norm hunk 无对应 · jump-delta #139 POP_JUMP_FORWARD_IF_FALSE to 298->to 464 (+166)
    - O  139 POP_JUMP_FORWARD_IF_FALSE to 298
    - P  139 POP_JUMP_FORWARD_IF_FALSE to 464
- **#3** `delete` orig[148:172] -> prod[148:148] · 对应 norm hunk [1]
    - O  148 JUMP_FORWARD to 348
    - O  149 LOAD_FAST flag
    - O  150 LOAD_CONST 1
    - O  151 COMPARE_OP ==
    - O  152 POP_JUMP_FORWARD_IF_FALSE to 322
    - O  153 LOAD_GLOBAL NULL + system_log
    - O  154 LOAD_ATTR debug
    - O  155 LOAD_GLOBAL NULL + _
    - O  156 LOAD_CONST "分笔数据转化异常，默认返回空值"
    - O  157 CALL
    - O  158 CALL
    - O  159 POP_TOP
    - O  160 JUMP_FORWARD to 344
    - O  161 LOAD_FAST flag
    - O  162 LOAD_CONST -1
    - O  163 COMPARE_OP ==
    - O  164 POP_JUMP_FORWARD_IF_FALSE to 344
    - O  165 LOAD_GLOBAL NULL + system_log
    - O  166 LOAD_ATTR debug
    - O  167 LOAD_GLOBAL NULL + _
    - O  168 LOAD_CONST "分笔数据返回空值"
    - O  169 CALL
    - O  170 CALL
    - O  171 POP_TOP
- **#4** `replace` orig[173:176] -> prod[149:150] · 对应 norm hunk [1]
    - O  173 RETURN_VALUE
    - O  174 LOAD_FAST redata
    - O  175 POP_JUMP_FORWARD_IF_FALSE to 448
    - P  149 POP_JUMP_FORWARD_IF_FALSE to 396
- **#5** `replace` orig[179:180] -> prod[153:154] · norm hunk 无对应
    - O  179 POP_JUMP_FORWARD_IF_FALSE to 364
    - P  153 POP_JUMP_FORWARD_IF_FALSE to 312
- **#6** `replace` orig[189:190] -> prod[163:164] · norm hunk 无对应
    - O  189 FOR_ITER to 444
    - P  163 FOR_ITER to 392
- **#7** `replace` orig[197:198] -> prod[171:172] · norm hunk 无对应
    - O  197 POP_JUMP_FORWARD_IF_TRUE to 420
    - P  171 POP_JUMP_FORWARD_IF_TRUE to 368
- **#8** `replace` orig[221:222] -> prod[195:196] · norm hunk 无对应
    - O  221 JUMP_BACKWARD to 378
    - P  195 JUMP_BACKWARD to 326
- **#9** `replace` orig[231:232] -> prod[205:206] · norm hunk 无对应
    - O  231 JUMP_FORWARD to 512
    - P  205 JUMP_FORWARD to 460
- **#10** `replace` orig[235:236] -> prod[209:210] · norm hunk 无对应 · jump-delta #235 POP_JUMP_FORWARD_IF_FALSE to 504->to 488 (-16)
    - O  235 POP_JUMP_FORWARD_IF_FALSE to 504
    - P  209 POP_JUMP_FORWARD_IF_FALSE to 452
- **#11** `replace` orig[247:248] -> prod[221:222] · norm hunk 无对应
    - O  247 JUMP_FORWARD to 512
    - P  221 JUMP_FORWARD to 460
- **#12** `insert` orig[258:258] -> prod[232:259] · 对应 norm hunk [2]
    - P  232 LOAD_FAST flag
    - P  233 LOAD_CONST 1
    - P  234 COMPARE_OP ==
    - P  235 POP_JUMP_FORWARD_IF_FALSE to 488
    - P  236 LOAD_GLOBAL NULL + system_log
    - P  237 LOAD_ATTR debug
    - P  238 LOAD_GLOBAL NULL + _
    - P  239 LOAD_CONST "分笔数据转化异常，默认返回空值"
    - P  240 CALL
    - P  241 CALL
    - P  242 POP_TOP
    - P  243 JUMP_FORWARD to 510
    - P  244 LOAD_FAST flag
    - P  245 LOAD_CONST -1
    - P  246 COMPARE_OP ==
    - P  247 POP_JUMP_FORWARD_IF_FALSE to 510
    - P  248 LOAD_GLOBAL NULL + system_log
    - P  249 LOAD_ATTR debug
    - P  250 LOAD_GLOBAL NULL + _
    - P  251 LOAD_CONST "分笔数据返回空值"
    - P  252 CALL
    - P  253 CALL
    - P  254 POP_TOP
    - P  255 LOAD_FAST redata
    - P  256 RETURN_VALUE
    - P  257 LOAD_CONST None
    - P  258 RETURN_VALUE

### arm=absj · hunks=12
- **#1** `replace` orig[4:5] -> prod[4:5] · norm hunk 无对应 · jump-delta #4 POP_JUMP_FORWARD_IF_FALSE to 512->to 514 (+2)
    - O    4 POP_JUMP_FORWARD_IF_FALSE to 512
    - P    4 POP_JUMP_FORWARD_IF_FALSE to 514
- **#2** `replace` orig[139:140] -> prod[139:140] · norm hunk 无对应 · jump-delta #139 POP_JUMP_FORWARD_IF_FALSE to 298->to 464 (+166)
    - O  139 POP_JUMP_FORWARD_IF_FALSE to 298
    - P  139 POP_JUMP_FORWARD_IF_FALSE to 464
- **#3** `delete` orig[148:172] -> prod[148:148] · 对应 norm hunk [1]
    - O  148 JUMP_FORWARD to 348
    - O  149 LOAD_FAST flag
    - O  150 LOAD_CONST 1
    - O  151 COMPARE_OP ==
    - O  152 POP_JUMP_FORWARD_IF_FALSE to 322
    - O  153 LOAD_GLOBAL NULL + system_log
    - O  154 LOAD_ATTR debug
    - O  155 LOAD_GLOBAL NULL + _
    - O  156 LOAD_CONST "分笔数据转化异常，默认返回空值"
    - O  157 CALL
    - O  158 CALL
    - O  159 POP_TOP
    - O  160 JUMP_FORWARD to 344
    - O  161 LOAD_FAST flag
    - O  162 LOAD_CONST -1
    - O  163 COMPARE_OP ==
    - O  164 POP_JUMP_FORWARD_IF_FALSE to 344
    - O  165 LOAD_GLOBAL NULL + system_log
    - O  166 LOAD_ATTR debug
    - O  167 LOAD_GLOBAL NULL + _
    - O  168 LOAD_CONST "分笔数据返回空值"
    - O  169 CALL
    - O  170 CALL
    - O  171 POP_TOP
- **#4** `replace` orig[173:176] -> prod[149:150] · 对应 norm hunk [1]
    - O  173 RETURN_VALUE
    - O  174 LOAD_FAST redata
    - O  175 POP_JUMP_FORWARD_IF_FALSE to 448
    - P  149 POP_JUMP_FORWARD_IF_FALSE to 396
- **#5** `replace` orig[179:180] -> prod[153:154] · norm hunk 无对应
    - O  179 POP_JUMP_FORWARD_IF_FALSE to 364
    - P  153 POP_JUMP_FORWARD_IF_FALSE to 312
- **#6** `replace` orig[189:190] -> prod[163:164] · norm hunk 无对应
    - O  189 FOR_ITER to 444
    - P  163 FOR_ITER to 392
- **#7** `replace` orig[197:198] -> prod[171:172] · norm hunk 无对应
    - O  197 POP_JUMP_FORWARD_IF_TRUE to 420
    - P  171 POP_JUMP_FORWARD_IF_TRUE to 368
- **#8** `replace` orig[221:222] -> prod[195:196] · norm hunk 无对应
    - O  221 JUMP_BACKWARD to 378
    - P  195 JUMP_BACKWARD to 326
- **#9** `replace` orig[231:232] -> prod[205:206] · norm hunk 无对应
    - O  231 JUMP_FORWARD to 512
    - P  205 JUMP_FORWARD to 460
- **#10** `replace` orig[235:236] -> prod[209:210] · norm hunk 无对应 · jump-delta #235 POP_JUMP_FORWARD_IF_FALSE to 504->to 488 (-16)
    - O  235 POP_JUMP_FORWARD_IF_FALSE to 504
    - P  209 POP_JUMP_FORWARD_IF_FALSE to 452
- **#11** `replace` orig[247:248] -> prod[221:222] · norm hunk 无对应
    - O  247 JUMP_FORWARD to 512
    - P  221 JUMP_FORWARD to 460
- **#12** `insert` orig[258:258] -> prod[232:259] · 对应 norm hunk [2]
    - P  232 LOAD_FAST flag
    - P  233 LOAD_CONST 1
    - P  234 COMPARE_OP ==
    - P  235 POP_JUMP_FORWARD_IF_FALSE to 488
    - P  236 LOAD_GLOBAL NULL + system_log
    - P  237 LOAD_ATTR debug
    - P  238 LOAD_GLOBAL NULL + _
    - P  239 LOAD_CONST "分笔数据转化异常，默认返回空值"
    - P  240 CALL
    - P  241 CALL
    - P  242 POP_TOP
    - P  243 JUMP_FORWARD to 510
    - P  244 LOAD_FAST flag
    - P  245 LOAD_CONST -1
    - P  246 COMPARE_OP ==
    - P  247 POP_JUMP_FORWARD_IF_FALSE to 510
    - P  248 LOAD_GLOBAL NULL + system_log
    - P  249 LOAD_ATTR debug
    - P  250 LOAD_GLOBAL NULL + _
    - P  251 LOAD_CONST "分笔数据返回空值"
    - P  252 CALL
    - P  253 CALL
    - P  254 POP_TOP
    - P  255 LOAD_FAST redata
    - P  256 RETURN_VALUE
    - P  257 LOAD_CONST None
    - P  258 RETURN_VALUE

### arm=absj3 · hunks=12
- **#1** `replace` orig[4:5] -> prod[4:5] · norm hunk 无对应 · jump-delta #4 POP_JUMP_FORWARD_IF_FALSE to 512->to 514 (+2)
    - O    4 POP_JUMP_FORWARD_IF_FALSE to 512
    - P    4 POP_JUMP_FORWARD_IF_FALSE to 514
- **#2** `replace` orig[139:140] -> prod[139:140] · norm hunk 无对应 · jump-delta #139 POP_JUMP_FORWARD_IF_FALSE to 298->to 464 (+166)
    - O  139 POP_JUMP_FORWARD_IF_FALSE to 298
    - P  139 POP_JUMP_FORWARD_IF_FALSE to 464
- **#3** `delete` orig[148:172] -> prod[148:148] · 对应 norm hunk [1]
    - O  148 JUMP_FORWARD to 348
    - O  149 LOAD_FAST flag
    - O  150 LOAD_CONST 1
    - O  151 COMPARE_OP ==
    - O  152 POP_JUMP_FORWARD_IF_FALSE to 322
    - O  153 LOAD_GLOBAL NULL + system_log
    - O  154 LOAD_ATTR debug
    - O  155 LOAD_GLOBAL NULL + _
    - O  156 LOAD_CONST "分笔数据转化异常，默认返回空值"
    - O  157 CALL
    - O  158 CALL
    - O  159 POP_TOP
    - O  160 JUMP_FORWARD to 344
    - O  161 LOAD_FAST flag
    - O  162 LOAD_CONST -1
    - O  163 COMPARE_OP ==
    - O  164 POP_JUMP_FORWARD_IF_FALSE to 344
    - O  165 LOAD_GLOBAL NULL + system_log
    - O  166 LOAD_ATTR debug
    - O  167 LOAD_GLOBAL NULL + _
    - O  168 LOAD_CONST "分笔数据返回空值"
    - O  169 CALL
    - O  170 CALL
    - O  171 POP_TOP
- **#4** `replace` orig[173:176] -> prod[149:150] · 对应 norm hunk [1]
    - O  173 RETURN_VALUE
    - O  174 LOAD_FAST redata
    - O  175 POP_JUMP_FORWARD_IF_FALSE to 448
    - P  149 POP_JUMP_FORWARD_IF_FALSE to 396
- **#5** `replace` orig[179:180] -> prod[153:154] · norm hunk 无对应
    - O  179 POP_JUMP_FORWARD_IF_FALSE to 364
    - P  153 POP_JUMP_FORWARD_IF_FALSE to 312
- **#6** `replace` orig[189:190] -> prod[163:164] · norm hunk 无对应
    - O  189 FOR_ITER to 444
    - P  163 FOR_ITER to 392
- **#7** `replace` orig[197:198] -> prod[171:172] · norm hunk 无对应
    - O  197 POP_JUMP_FORWARD_IF_TRUE to 420
    - P  171 POP_JUMP_FORWARD_IF_TRUE to 368
- **#8** `replace` orig[221:222] -> prod[195:196] · norm hunk 无对应
    - O  221 JUMP_BACKWARD to 378
    - P  195 JUMP_BACKWARD to 326
- **#9** `replace` orig[231:232] -> prod[205:206] · norm hunk 无对应
    - O  231 JUMP_FORWARD to 512
    - P  205 JUMP_FORWARD to 460
- **#10** `replace` orig[235:236] -> prod[209:210] · norm hunk 无对应 · jump-delta #235 POP_JUMP_FORWARD_IF_FALSE to 504->to 488 (-16)
    - O  235 POP_JUMP_FORWARD_IF_FALSE to 504
    - P  209 POP_JUMP_FORWARD_IF_FALSE to 452
- **#11** `replace` orig[247:248] -> prod[221:222] · norm hunk 无对应
    - O  247 JUMP_FORWARD to 512
    - P  221 JUMP_FORWARD to 460
- **#12** `insert` orig[258:258] -> prod[232:259] · 对应 norm hunk [2]
    - P  232 LOAD_FAST flag
    - P  233 LOAD_CONST 1
    - P  234 COMPARE_OP ==
    - P  235 POP_JUMP_FORWARD_IF_FALSE to 488
    - P  236 LOAD_GLOBAL NULL + system_log
    - P  237 LOAD_ATTR debug
    - P  238 LOAD_GLOBAL NULL + _
    - P  239 LOAD_CONST "分笔数据转化异常，默认返回空值"
    - P  240 CALL
    - P  241 CALL
    - P  242 POP_TOP
    - P  243 JUMP_FORWARD to 510
    - P  244 LOAD_FAST flag
    - P  245 LOAD_CONST -1
    - P  246 COMPARE_OP ==
    - P  247 POP_JUMP_FORWARD_IF_FALSE to 510
    - P  248 LOAD_GLOBAL NULL + system_log
    - P  249 LOAD_ATTR debug
    - P  250 LOAD_GLOBAL NULL + _
    - P  251 LOAD_CONST "分笔数据返回空值"
    - P  252 CALL
    - P  253 CALL
    - P  254 POP_TOP
    - P  255 LOAD_FAST redata
    - P  256 RETURN_VALUE
    - P  257 LOAD_CONST None
    - P  258 RETURN_VALUE

### arm=absj9 · hunks=5
- **#1** `replace` orig[4:5] -> prod[4:5] · norm hunk 无对应 · jump-delta #4 POP_JUMP_FORWARD_IF_FALSE to 512->to 516 (+4)
    - O    4 POP_JUMP_FORWARD_IF_FALSE to 512
    - P    4 POP_JUMP_FORWARD_IF_FALSE to 516
- **#2** `replace` orig[231:232] -> prod[231:233] · 对应 norm hunk [1]
    - O  231 JUMP_FORWARD to 512
    - P  231 LOAD_CONST None
    - P  232 RETURN_VALUE
- **#3** `replace` orig[235:236] -> prod[236:237] · norm hunk 无对应
    - O  235 POP_JUMP_FORWARD_IF_FALSE to 504
    - P  236 POP_JUMP_FORWARD_IF_FALSE to 508
- **#4** `replace` orig[247:248] -> prod[248:250] · 对应 norm hunk [2]
    - O  247 JUMP_FORWARD to 512
    - P  248 LOAD_CONST None
    - P  249 RETURN_VALUE
- **#5** `replace` orig[256:257] -> prod[258:259] · 对应 norm hunk [3]
    - O  256 LOAD_FAST pd_dict
    - P  258 LOAD_CONST None

### arm=absjt · hunks=5
- **#1** `replace` orig[4:5] -> prod[4:5] · norm hunk 无对应 · jump-delta #4 POP_JUMP_FORWARD_IF_FALSE to 512->to 516 (+4)
    - O    4 POP_JUMP_FORWARD_IF_FALSE to 512
    - P    4 POP_JUMP_FORWARD_IF_FALSE to 516
- **#2** `replace` orig[231:232] -> prod[231:233] · 对应 norm hunk [1]
    - O  231 JUMP_FORWARD to 512
    - P  231 LOAD_CONST None
    - P  232 RETURN_VALUE
- **#3** `replace` orig[235:236] -> prod[236:237] · norm hunk 无对应
    - O  235 POP_JUMP_FORWARD_IF_FALSE to 504
    - P  236 POP_JUMP_FORWARD_IF_FALSE to 508
- **#4** `replace` orig[247:248] -> prod[248:250] · 对应 norm hunk [2]
    - O  247 JUMP_FORWARD to 512
    - P  248 LOAD_CONST None
    - P  249 RETURN_VALUE
- **#5** `replace` orig[256:257] -> prod[258:259] · 对应 norm hunk [3]
    - O  256 LOAD_FAST pd_dict
    - P  258 LOAD_CONST None

### arm=try7_9 · hunks=5
- **#1** `replace` orig[4:5] -> prod[4:5] · norm hunk 无对应 · jump-delta #4 POP_JUMP_FORWARD_IF_FALSE to 512->to 516 (+4)
    - O    4 POP_JUMP_FORWARD_IF_FALSE to 512
    - P    4 POP_JUMP_FORWARD_IF_FALSE to 516
- **#2** `replace` orig[231:232] -> prod[231:233] · 对应 norm hunk [1]
    - O  231 JUMP_FORWARD to 512
    - P  231 LOAD_CONST None
    - P  232 RETURN_VALUE
- **#3** `replace` orig[235:236] -> prod[236:237] · norm hunk 无对应
    - O  235 POP_JUMP_FORWARD_IF_FALSE to 504
    - P  236 POP_JUMP_FORWARD_IF_FALSE to 508
- **#4** `replace` orig[247:248] -> prod[248:250] · 对应 norm hunk [2]
    - O  247 JUMP_FORWARD to 512
    - P  248 LOAD_CONST None
    - P  249 RETURN_VALUE
- **#5** `replace` orig[256:257] -> prod[258:259] · 对应 norm hunk [3]
    - O  256 LOAD_FAST pd_dict
    - P  258 LOAD_CONST None

### arm=try7_10d · hunks=5
- **#1** `replace` orig[4:5] -> prod[4:5] · norm hunk 无对应 · jump-delta #4 POP_JUMP_FORWARD_IF_FALSE to 512->to 516 (+4)
    - O    4 POP_JUMP_FORWARD_IF_FALSE to 512
    - P    4 POP_JUMP_FORWARD_IF_FALSE to 516
- **#2** `replace` orig[231:232] -> prod[231:233] · 对应 norm hunk [1]
    - O  231 JUMP_FORWARD to 512
    - P  231 LOAD_CONST None
    - P  232 RETURN_VALUE
- **#3** `replace` orig[235:236] -> prod[236:237] · norm hunk 无对应
    - O  235 POP_JUMP_FORWARD_IF_FALSE to 504
    - P  236 POP_JUMP_FORWARD_IF_FALSE to 508
- **#4** `replace` orig[247:248] -> prod[248:250] · 对应 norm hunk [2]
    - O  247 JUMP_FORWARD to 512
    - P  248 LOAD_CONST None
    - P  249 RETURN_VALUE
- **#5** `replace` orig[256:257] -> prod[258:259] · 对应 norm hunk [3]
    - O  256 LOAD_FAST pd_dict
    - P  258 LOAD_CONST None

### arm=try7_3 · hunks=12
- **#1** `replace` orig[4:5] -> prod[4:5] · norm hunk 无对应 · jump-delta #4 POP_JUMP_FORWARD_IF_FALSE to 512->to 514 (+2)
    - O    4 POP_JUMP_FORWARD_IF_FALSE to 512
    - P    4 POP_JUMP_FORWARD_IF_FALSE to 514
- **#2** `replace` orig[139:140] -> prod[139:140] · norm hunk 无对应 · jump-delta #139 POP_JUMP_FORWARD_IF_FALSE to 298->to 464 (+166)
    - O  139 POP_JUMP_FORWARD_IF_FALSE to 298
    - P  139 POP_JUMP_FORWARD_IF_FALSE to 464
- **#3** `delete` orig[148:172] -> prod[148:148] · 对应 norm hunk [1]
    - O  148 JUMP_FORWARD to 348
    - O  149 LOAD_FAST flag
    - O  150 LOAD_CONST 1
    - O  151 COMPARE_OP ==
    - O  152 POP_JUMP_FORWARD_IF_FALSE to 322
    - O  153 LOAD_GLOBAL NULL + system_log
    - O  154 LOAD_ATTR debug
    - O  155 LOAD_GLOBAL NULL + _
    - O  156 LOAD_CONST "分笔数据转化异常，默认返回空值"
    - O  157 CALL
    - O  158 CALL
    - O  159 POP_TOP
    - O  160 JUMP_FORWARD to 344
    - O  161 LOAD_FAST flag
    - O  162 LOAD_CONST -1
    - O  163 COMPARE_OP ==
    - O  164 POP_JUMP_FORWARD_IF_FALSE to 344
    - O  165 LOAD_GLOBAL NULL + system_log
    - O  166 LOAD_ATTR debug
    - O  167 LOAD_GLOBAL NULL + _
    - O  168 LOAD_CONST "分笔数据返回空值"
    - O  169 CALL
    - O  170 CALL
    - O  171 POP_TOP
- **#4** `replace` orig[173:176] -> prod[149:150] · 对应 norm hunk [1]
    - O  173 RETURN_VALUE
    - O  174 LOAD_FAST redata
    - O  175 POP_JUMP_FORWARD_IF_FALSE to 448
    - P  149 POP_JUMP_FORWARD_IF_FALSE to 396
- **#5** `replace` orig[179:180] -> prod[153:154] · norm hunk 无对应
    - O  179 POP_JUMP_FORWARD_IF_FALSE to 364
    - P  153 POP_JUMP_FORWARD_IF_FALSE to 312
- **#6** `replace` orig[189:190] -> prod[163:164] · norm hunk 无对应
    - O  189 FOR_ITER to 444
    - P  163 FOR_ITER to 392
- **#7** `replace` orig[197:198] -> prod[171:172] · norm hunk 无对应
    - O  197 POP_JUMP_FORWARD_IF_TRUE to 420
    - P  171 POP_JUMP_FORWARD_IF_TRUE to 368
- **#8** `replace` orig[221:222] -> prod[195:196] · norm hunk 无对应
    - O  221 JUMP_BACKWARD to 378
    - P  195 JUMP_BACKWARD to 326
- **#9** `replace` orig[231:232] -> prod[205:206] · norm hunk 无对应
    - O  231 JUMP_FORWARD to 512
    - P  205 JUMP_FORWARD to 460
- **#10** `replace` orig[235:236] -> prod[209:210] · norm hunk 无对应 · jump-delta #235 POP_JUMP_FORWARD_IF_FALSE to 504->to 488 (-16)
    - O  235 POP_JUMP_FORWARD_IF_FALSE to 504
    - P  209 POP_JUMP_FORWARD_IF_FALSE to 452
- **#11** `replace` orig[247:248] -> prod[221:222] · norm hunk 无对应
    - O  247 JUMP_FORWARD to 512
    - P  221 JUMP_FORWARD to 460
- **#12** `insert` orig[258:258] -> prod[232:259] · 对应 norm hunk [2]
    - P  232 LOAD_FAST flag
    - P  233 LOAD_CONST 1
    - P  234 COMPARE_OP ==
    - P  235 POP_JUMP_FORWARD_IF_FALSE to 488
    - P  236 LOAD_GLOBAL NULL + system_log
    - P  237 LOAD_ATTR debug
    - P  238 LOAD_GLOBAL NULL + _
    - P  239 LOAD_CONST "分笔数据转化异常，默认返回空值"
    - P  240 CALL
    - P  241 CALL
    - P  242 POP_TOP
    - P  243 JUMP_FORWARD to 510
    - P  244 LOAD_FAST flag
    - P  245 LOAD_CONST -1
    - P  246 COMPARE_OP ==
    - P  247 POP_JUMP_FORWARD_IF_FALSE to 510
    - P  248 LOAD_GLOBAL NULL + system_log
    - P  249 LOAD_ATTR debug
    - P  250 LOAD_GLOBAL NULL + _
    - P  251 LOAD_CONST "分笔数据返回空值"
    - P  252 CALL
    - P  253 CALL
    - P  254 POP_TOP
    - P  255 LOAD_FAST redata
    - P  256 RETURN_VALUE
    - P  257 LOAD_CONST None
    - P  258 RETURN_VALUE

## 4. 字节级内容（matched 指令表：`idx` / `offset` / `co_code` 字节；与 §2、§3 的 index 完全同一空间）

### orig（matched，len=258）· 三个归一化 hunk 的 orig 侧
- hunk #1 `delete` orig[148:174]
-  148 off=296           JUMP_FORWARD                                 to 348
-  149 off=298           LOAD_FAST                                    flag
-  150 off=300           LOAD_CONST                                   1
-  151 off=302           COMPARE_OP                                   ==
-  152 off=304           POP_JUMP_FORWARD_IF_FALSE                    to 322
-  153 off=306           LOAD_GLOBAL                                  NULL + system_log
-  154 off=308           LOAD_ATTR                                    debug
-  155 off=310           LOAD_GLOBAL                                  NULL + _
-  156 off=312           LOAD_CONST                                   "分笔数据转化异常，默认返回空值"
-  157 off=314           CALL                                         
-  158 off=316           CALL                                         
-  159 off=318           POP_TOP                                      
-  160 off=320           JUMP_FORWARD                                 to 344
-  161 off=322           LOAD_FAST                                    flag
-  162 off=324           LOAD_CONST                                   -1
-  163 off=326           COMPARE_OP                                   ==
-  164 off=328           POP_JUMP_FORWARD_IF_FALSE                    to 344
-  165 off=330           LOAD_GLOBAL                                  NULL + system_log
-  166 off=332           LOAD_ATTR                                    debug
-  167 off=334           LOAD_GLOBAL                                  NULL + _
-  168 off=336           LOAD_CONST                                   "分笔数据返回空值"
-  169 off=338           CALL                                         
-  170 off=340           CALL                                         
-  171 off=342           POP_TOP                                      
-  172 off=344           LOAD_FAST                                    redata
-  173 off=346           RETURN_VALUE                                 
- hunk #2 `insert` orig[258:258]

### arm=landed（matched，len=259）· hunks_norm=2
- hunk #1 `delete` -> prod[148:148]
- hunk #2 `insert` -> prod[232:259]
-  232 off=464           LOAD_FAST                                    flag
-  233 off=466           LOAD_CONST                                   1
-  234 off=468           COMPARE_OP                                   ==
-  235 off=470           POP_JUMP_FORWARD_IF_FALSE                    to 488
-  236 off=472           LOAD_GLOBAL                                  NULL + system_log
-  237 off=474           LOAD_ATTR                                    debug
-  238 off=476           LOAD_GLOBAL                                  NULL + _
-  239 off=478           LOAD_CONST                                   "分笔数据转化异常，默认返回空值"
-  240 off=480           CALL                                         
-  241 off=482           CALL                                         
-  242 off=484           POP_TOP                                      
-  243 off=486           JUMP_FORWARD                                 to 510
-  244 off=488           LOAD_FAST                                    flag
-  245 off=490           LOAD_CONST                                   -1
-  246 off=492           COMPARE_OP                                   ==
-  247 off=494           POP_JUMP_FORWARD_IF_FALSE                    to 510
-  248 off=496           LOAD_GLOBAL                                  NULL + system_log
-  249 off=498           LOAD_ATTR                                    debug
-  250 off=500           LOAD_GLOBAL                                  NULL + _
-  251 off=502           LOAD_CONST                                   "分笔数据返回空值"
-  252 off=504           CALL                                         
-  253 off=506           CALL                                         
-  254 off=508           POP_TOP                                      
-  255 off=510           LOAD_FAST                                    redata
-  256 off=512           RETURN_VALUE                                 
-  257 off=514           LOAD_CONST                                   None
-  258 off=516           RETURN_VALUE                                 

### arm=absj（matched，len=259）· hunks_norm=2
- hunk #1 `delete` -> prod[148:148]
- hunk #2 `insert` -> prod[232:259]
-  232 off=464           LOAD_FAST                                    flag
-  233 off=466           LOAD_CONST                                   1
-  234 off=468           COMPARE_OP                                   ==
-  235 off=470           POP_JUMP_FORWARD_IF_FALSE                    to 488
-  236 off=472           LOAD_GLOBAL                                  NULL + system_log
-  237 off=474           LOAD_ATTR                                    debug
-  238 off=476           LOAD_GLOBAL                                  NULL + _
-  239 off=478           LOAD_CONST                                   "分笔数据转化异常，默认返回空值"
-  240 off=480           CALL                                         
-  241 off=482           CALL                                         
-  242 off=484           POP_TOP                                      
-  243 off=486           JUMP_FORWARD                                 to 510
-  244 off=488           LOAD_FAST                                    flag
-  245 off=490           LOAD_CONST                                   -1
-  246 off=492           COMPARE_OP                                   ==
-  247 off=494           POP_JUMP_FORWARD_IF_FALSE                    to 510
-  248 off=496           LOAD_GLOBAL                                  NULL + system_log
-  249 off=498           LOAD_ATTR                                    debug
-  250 off=500           LOAD_GLOBAL                                  NULL + _
-  251 off=502           LOAD_CONST                                   "分笔数据返回空值"
-  252 off=504           CALL                                         
-  253 off=506           CALL                                         
-  254 off=508           POP_TOP                                      
-  255 off=510           LOAD_FAST                                    redata
-  256 off=512           RETURN_VALUE                                 
-  257 off=514           LOAD_CONST                                   None
-  258 off=516           RETURN_VALUE                                 

### arm=absj3（matched，len=259）· hunks_norm=2
- hunk #1 `delete` -> prod[148:148]
- hunk #2 `insert` -> prod[232:259]
-  232 off=464           LOAD_FAST                                    flag
-  233 off=466           LOAD_CONST                                   1
-  234 off=468           COMPARE_OP                                   ==
-  235 off=470           POP_JUMP_FORWARD_IF_FALSE                    to 488
-  236 off=472           LOAD_GLOBAL                                  NULL + system_log
-  237 off=474           LOAD_ATTR                                    debug
-  238 off=476           LOAD_GLOBAL                                  NULL + _
-  239 off=478           LOAD_CONST                                   "分笔数据转化异常，默认返回空值"
-  240 off=480           CALL                                         
-  241 off=482           CALL                                         
-  242 off=484           POP_TOP                                      
-  243 off=486           JUMP_FORWARD                                 to 510
-  244 off=488           LOAD_FAST                                    flag
-  245 off=490           LOAD_CONST                                   -1
-  246 off=492           COMPARE_OP                                   ==
-  247 off=494           POP_JUMP_FORWARD_IF_FALSE                    to 510
-  248 off=496           LOAD_GLOBAL                                  NULL + system_log
-  249 off=498           LOAD_ATTR                                    debug
-  250 off=500           LOAD_GLOBAL                                  NULL + _
-  251 off=502           LOAD_CONST                                   "分笔数据返回空值"
-  252 off=504           CALL                                         
-  253 off=506           CALL                                         
-  254 off=508           POP_TOP                                      
-  255 off=510           LOAD_FAST                                    redata
-  256 off=512           RETURN_VALUE                                 
-  257 off=514           LOAD_CONST                                   None
-  258 off=516           RETURN_VALUE                                 

### arm=absj9（matched，len=260）· hunks_norm=3
- hunk #1 `replace` -> prod[231:233]
-  231 off=462           LOAD_CONST                                   None
-  232 off=464           RETURN_VALUE                                 
- hunk #2 `replace` -> prod[248:250]
-  248 off=496           LOAD_CONST                                   None
-  249 off=498           RETURN_VALUE                                 
- hunk #3 `replace` -> prod[258:259]
-  258 off=516           LOAD_CONST                                   None

### arm=absjt（matched，len=260）· hunks_norm=3
- hunk #1 `replace` -> prod[231:233]
-  231 off=462           LOAD_CONST                                   None
-  232 off=464           RETURN_VALUE                                 
- hunk #2 `replace` -> prod[248:250]
-  248 off=496           LOAD_CONST                                   None
-  249 off=498           RETURN_VALUE                                 
- hunk #3 `replace` -> prod[258:259]
-  258 off=516           LOAD_CONST                                   None

### arm=try7_9（matched，len=260）· hunks_norm=3
- hunk #1 `replace` -> prod[231:233]
-  231 off=462           LOAD_CONST                                   None
-  232 off=464           RETURN_VALUE                                 
- hunk #2 `replace` -> prod[248:250]
-  248 off=496           LOAD_CONST                                   None
-  249 off=498           RETURN_VALUE                                 
- hunk #3 `replace` -> prod[258:259]
-  258 off=516           LOAD_CONST                                   None

### arm=try7_10d（matched，len=260）· hunks_norm=3
- hunk #1 `replace` -> prod[231:233]
-  231 off=462           LOAD_CONST                                   None
-  232 off=464           RETURN_VALUE                                 
- hunk #2 `replace` -> prod[248:250]
-  248 off=496           LOAD_CONST                                   None
-  249 off=498           RETURN_VALUE                                 
- hunk #3 `replace` -> prod[258:259]
-  258 off=516           LOAD_CONST                                   None

### arm=try7_3（matched，len=259）· hunks_norm=2
- hunk #1 `delete` -> prod[148:148]
- hunk #2 `insert` -> prod[232:259]
-  232 off=464           LOAD_FAST                                    flag
-  233 off=466           LOAD_CONST                                   1
-  234 off=468           COMPARE_OP                                   ==
-  235 off=470           POP_JUMP_FORWARD_IF_FALSE                    to 488
-  236 off=472           LOAD_GLOBAL                                  NULL + system_log
-  237 off=474           LOAD_ATTR                                    debug
-  238 off=476           LOAD_GLOBAL                                  NULL + _
-  239 off=478           LOAD_CONST                                   "分笔数据转化异常，默认返回空值"
-  240 off=480           CALL                                         
-  241 off=482           CALL                                         
-  242 off=484           POP_TOP                                      
-  243 off=486           JUMP_FORWARD                                 to 510
-  244 off=488           LOAD_FAST                                    flag
-  245 off=490           LOAD_CONST                                   -1
-  246 off=492           COMPARE_OP                                   ==
-  247 off=494           POP_JUMP_FORWARD_IF_FALSE                    to 510
-  248 off=496           LOAD_GLOBAL                                  NULL + system_log
-  249 off=498           LOAD_ATTR                                    debug
-  250 off=500           LOAD_GLOBAL                                  NULL + _
-  251 off=502           LOAD_CONST                                   "分笔数据返回空值"
-  252 off=504           CALL                                         
-  253 off=506           CALL                                         
-  254 off=508           POP_TOP                                      
-  255 off=510           LOAD_FAST                                    redata
-  256 off=512           RETURN_VALUE                                 
-  257 off=514           LOAD_CONST                                   None
-  258 off=516           RETURN_VALUE                                 


---

## 5. 解剖结论（diag1 判读）

### 5.1 三个臂到底各改了哪些 hunk

| 臂 | spec | tick_direction 指标 | 相对 landed 的改动 |
|---|---|---|---|
| absj | `abs1`+`abs2_orphan_child_emit` | hunks 12 / norm 2 / first 4 / sd 184 | 该单元**零变化** |
| absj3 | absj + `try7_3`（5 edits：`78eea71b` T1/T2、`343e05ae` T4、`66486c1d`、`0b10b201`、`861c978c` T6） | hunks 12 / norm 2 / first 4 / sd 184 | 该单元**零变化**（指标与 landed 逐位相同） |
| absj9 | absj + `try7_9`（7 edits = try7_3 的 5 处 + **`31b0d3fa` `_try_has_return` 守卫** + **`2b9410cc` T7**） | hunks 5 / norm **3** / first 4 / sd **4** | 结构被改写，见 5.2 |
| absjt / try7_10d | absj + `try7_10d`（同 7 处，`31b0d3fa` 换成 2931 B 长版、带 BDBG 调试输出） | hunks 5 / norm 3 / first 4 / sd 4 | 与 absj9 在本单元**读数完全相同** |

- 即：`try7_3` 完全不含这两处新增编辑，所以 **absj3 过 ADR-1 是因为它根本没碰这个单元的形状**，不是因为它在该单元上做得更好。
- 真正改变本单元的是 `try7_9`/`try7_10d` 新增的 2 处编辑；两者在本单元产生逐位相同的读数，因此**第 2 处编辑（T7，`2b9410cc`）足以复现该回退**；第 1 处（`_try_has_return` 守卫）是否单独致回退未隔离（diag1 只读，不做建臂实验，留 fix1 隔离：`absj+edit5` 与 `absj+edit6` 各建一臂跑 ADR）。

### 5.2 结构被改成了什么（`build_landed` vs `build_absj9` 源码差，78 行 vs 78 行）

```diff
-                try:                                   |            else:
-                    if redata:                          |                if flag == 1:
-                        if tick_direction_in_dict=='1': |                    system_log.debug(...)
-                            return redata               |                elif flag == -1:
-                        ...                             |                    system_log.debug(...)
-                        return pd_dict                  |                return redata
-                    else:                               |            try:
-                        system_log.debug(...)           |                if redata:
-                except Exception as e:                  |                    ...
-                    system_log.debug(get_traceback_message())
-                return pd_dict                      |            except Exception as e:
-            elif flag == 1: ...                    |                system_log.debug(...)
-            elif flag == -1: ...                   |
-            return redata                          |
```

- landed：`if redata:` 链把 `flag==1 / flag==-1 / return redata` 当成**同级 `elif`** 挂在 try 外侧（结构错，`return pd_dict` 停在 if 链内）。
- absj9（T7）：改成 `if A: P else: <flag 链>; return redata`，try 从 if 链里切出、在链后重发——**这正是 T7 注释描述的原始结构**，因此 `sdelta 184→4`、`hunks 12→5`（三条跳转差只剩 1 条 `to 512→to 516 (+4)`）。
- 代价：切出/重发后，**尾部共享 `return pd_dict` 没有被重新发射**，产品函数尾变成 `return redata` + 隐式 `return None`。

### 5.3 第 3 个（以及前两个）归一化 hunk 的字节内容

matched 空间（`idx / offset / opname`），orig vs `absj9`：

| # | 归一化 hunk | orig | absj9 产品 | 字节 |
|---|---|---|---|---|
| 1 | replace | `231 JUMP_FORWARD to 512` | `231 LOAD_CONST None` + `232 RETURN_VALUE` | 跳转被物化成 `return None` |
| 2 | replace | `247 JUMP_FORWARD to 512`（except 清理后 `DELETE_FAST e` → 跳共享尾） | `248 LOAD_CONST None` + `249 RETURN_VALUE` | 同上，字节 `6400 5300`（`LOAD_CONST None; RETURN_VALUE` @496/498） |
| 3 | replace | `256 LOAD_FAST pd_dict` @512 → `257 RETURN_VALUE` @514 | `258 LOAD_CONST None` @516 → `259 RETURN_VALUE` @518 | 尾部返回值 `pd_dict`→`None`，字节 `7c08 5300`（orig）vs `6400 5300`（产品） |

三条 hunk 全部是同一件事的三个投影：**产品少了「共享尾 `return pd_dict`」**，于是
两个前跳出口物化成 `return None`、最后一跳的返回值变 `None`。

### 5.4 为什么 absj 过、`+try7_9`/`+try7_10d` 不过

1. landed/absj/absj3 的 2 个归一化 hunk 是「整块搬移」形状（`delete orig[148:174]` + `insert prod[232:259]`）——SequenceMatcher 把错位的 flag 块当作一个 replace/delete 对，**尾部 `return pd_dict` 的差异被包进这个 insert 段里，不再单独计数**。
2. T7 把结构摆正后，大块搬移消失（hunks 12→5、sd 184→4），剩下 3 处**真实的出口差异**被逐个计为独立 hunk ⇒ `hunks_norm 2→3`。
3. ADR-1 是「任一指标变差即整件拒收」：`hunks ✓ 12→5`、`sdelta ✓ 184→4`、`first_diff = 4→4` 都不触发，只有 `hunks_norm 2→3` 触发 ⇒ 拒收。

**判读**：该回退是 **ADR-1 的计分形状效应（把『搬移』记成 1 个 hunk、把『修好的结构 + 3 处真实出口差』记成 3 个 hunk）叠加一个真实缺陷（共享尾 `return pd_dict` 未重新发射）**。
fix1 的正确姿势不是放弃 T7，而是**给 T7 补上尾部共享块的重发射**（或按 `handlers._target` 已验证的行表判据：不物化编译器生成的 `return None`、让各出口 `JUMP_FORWARD` 到共享尾），使 `hunks_norm ≤ 2` 后重跑 ADR-1。

# -*- coding: utf-8 -*-
"""Prepend the measured G0 header to the two Round-30 repro sources and normalise them to
pure CRLF (the convention of test_repros/round29_*)."""
import io
import os

D = r'F:\Downloads\pythoncdc-main\test_repros\round30_enclosing_loop_backedge_break'

H_W2 = u'''# Round 30 G0 WITNESS battery for candidate R30-C1 —— 内层 loop 的 break 角色核验抢走
# 「承载外层 loop 回边」的那一块（原则 2 每块唯一归属的 break-role 侧；只删不增）。
# MEASURED on both cores (mirror root D:/Temp/r30gate/c1, `python -X utf8 r30c.py run`):
#   landed core   r30c_w2.pyc  matched 3/6
#     mism = [['w_a_true_break_epilogue', 27, 21, 1, 11],
#             ['w_b_true_break_yield_epilogue', 23, 19, 0, 23],
#             ['w_e_deep', 30, 26, 0, 30]]
#   + R30-C1      r30c_w2.pyc  matched 6/6, mism=[]
#                  产物 sha d17b0ae28839af5e -> 82e204835d56eeed
# 三个缺陷函数的共同形状：外层 for 的循环体在**嵌套 while 之后**还有语句，承载那些尾语句的
# 块以「向后跳到 for 头部」结尾 —— 该终止指令是外层 loop 的回边，不是内层 loop 的 break 出口，
# 但内层的 break 核验仍把它收进区域块集，内层渲染的批量入账随即令它无人发射。
# w_c_for_break_yield / w_d_try_inside 原以为是同族见证，实测两核均 6/6 干净：
# 「嵌套 loop 之后的任意块」这条拇指规则太弱，起作用的是**向后跳转终止指令**本身。
# 记为负结果，不算通过的见证。

'''

H_CTL = u'''# Round 30 CONTROL battery for R30-C1 —— 判据邻位的四个结构形状，必须逐字节不动。
# MEASURED: landed core 与 R30-C1 两侧均 matched 6/6、mism=[]，且两份产物 **sha 逐字节相同**
# （ef52a76276145780）⇒ 该判据可证不触及：(a) 内层 loop 自己的回边（终止指令跳向**本**头部）、
# (b) 真 break（终止指令是向前跳转）、(c) for 套 for 的 break、(d) while True 破出且区域出口块
# 之后无块。注意：本文件里的 `witness` 函数是那 6 个匹配函数之一，它是 CONTROL 不是见证 ——
# 会失败的中心形状在 r30c_w2.pyc。

'''

for name, header in (('r30c_w2.py', H_W2), ('r30c_witness.py', H_CTL)):
    p = os.path.join(D, name)
    raw = io.open(p, 'rb').read()
    assert raw[:3] != b'\xef\xbb\xbf', name
    assert b'\r' not in raw, name + ' already has CR'
    text = raw.decode('utf-8')
    if text.startswith('# -*- coding: utf-8 -*-\n'):
        text = text[len('# -*- coding: utf-8 -*-\n'):]
    out = (u'# -*- coding: utf-8 -*-\n' + header + text).replace('\n', '\r\n')
    assert out.count('\r\n') == out.count('\n') and '\r\r\n' not in out
    io.open(p, 'wb').write(out.encode('utf-8'))
    print('%s -> %d bytes, %d CRLF lines' % (name, len(out.encode('utf-8')), out.count('\r\n')))

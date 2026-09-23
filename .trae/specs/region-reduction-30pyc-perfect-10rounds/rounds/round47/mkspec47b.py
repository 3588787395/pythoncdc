# -*- coding: utf-8 -*-
"""Derive spec_r47b.json: fold a try-body held-value Expr into the lone RETURN_VALUE block.

Asserts the anchor is unique in the CURRENT landed bytes and reports the line delta.
"""
import io
import json

REPO = r'F:\Downloads\pythoncdc-main'
REL = 'core/cfg/region_ast_generator.py'
OUT = r'D:/Temp/r47mine/spec_r47b.json'

anchor = """                stmts = self._generate_block_statements(block)
                body_stmts.extend(stmts)
                self.generated_blocks.add(block)"""

doc = """                # 区域归约算法原则 1（每块＝前导语句 + 唯一终止指令）＋ 原则 2（每块唯一归属）：
                # try 体的保护跨度会把「压值指令」与它的消费者 RETURN_VALUE 切成相邻两块：
                # 前块以 LOAD_* 结尾（值被持有、块内无消费者、纯落空到下一块），本块只含一条
                # RETURN_VALUE。逐块独立发射时前块的持有值退化成 Expr 语句（编译为
                # 「<值> POP_TOP」），本块退化成 `return None`（编译为
                # 「LOAD_CONST None; RETURN_VALUE」），合起来比原始字节码多出 POP_TOP 与
                # LOAD_CONST 两条指令。
                # 同层判据（只读结构事实，不读名字/常量/绝对偏移/指令条数/函数名）：
                #   ① 本块的有意义指令恰为一条 RETURN_VALUE（纯终止符块，无块内语句）；
                #   ② 本块无后继，且唯一前驱 P 以正常后继指向本块（纯落空，非跳转分叉）；
                #   ③ P 属本 try 区域的受保护块集，且 P 的末条指令是 LOAD_*（持有值）；
                #   ④ 刚生成本块语句表恰为一条 Return(Constant(None))，且不带
                #      _explicit_return 标记（是合成的收尾返回，不是源码里的显式 return）；
                #   ⑤ try 体此刻已发射语句的末条是 Expr（正是 P 块那个被丢弃的持有值）。
                # 归约方式：把该 Expr 的值升格为 Return 的值（原则 1：终止符随其块的前导值
                # 一起归约为一条 return 语句），本块随之不再独立发射。
                # 危害形态：site-packages/fly/data/quote_handler.pyc ::
                #   <module>.get_Ashares_local 75/77 —— try 体末尾的 `return returnlist`
                #   被拆成 `returnlist` + `return None`。
                # 不命中即逐字节沿用原路径：非纯终止符块、非落空、显式 return、
                # 以及前块末条不是 LOAD_* 的情形（如裸 `return`、`foo(); return`）全部不变。"""

code = """                _r47_p47 = None
                _r47_m47 = [i for i in block.instructions
                            if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                if (len(_r47_m47) == 1 and _r47_m47[0].opname == 'RETURN_VALUE'
                        and len(block.predecessors or []) == 1
                        and not (block.successors or [])):
                    _r47_p47 = (block.predecessors or [])[0]
                _r47_plast = _r47_p47.get_last_instruction() if _r47_p47 is not None else None
                if (_r47_p47 is not None and _r47_p47 in set(region.try_blocks)
                        and len(_r47_p47.successors or []) == 1
                        and _r47_p47.successors[0] is block
                        and _r47_plast is not None
                        and str(_r47_plast.opname).startswith('LOAD_')
                        and len(stmts) == 1 and isinstance(stmts[0], dict)
                        and stmts[0].get('type') == 'Return'
                        and not stmts[0].get('_explicit_return')
                        and isinstance(stmts[0].get('value'), dict)
                        and stmts[0]['value'].get('type') == 'Constant'
                        and stmts[0]['value'].get('value') is None
                        and body_stmts and isinstance(body_stmts[-1], dict)
                        and body_stmts[-1].get('type') == 'Expr'
                        and isinstance(body_stmts[-1].get('value'), dict)):
                    body_stmts[-1] = {'type': 'Return',
                                      'value': body_stmts[-1]['value']}
                    stmts = []"""

repl = ('                stmts = self._generate_block_statements(block)\n'
        + doc + '\n' + code + '\n'
        + '                body_stmts.extend(stmts)\n'
        + '                self.generated_blocks.add(block)')

p = REPO + '/' + REL
raw = io.open(p, 'rb').read()
assert raw[:3] == b'\xef\xbb\xbf', 'generator lost its BOM'
u = raw.decode('utf-8-sig').replace('\r\n', '\n')
n = u.count(anchor)
assert n == 1, 'anchor occurrences = %d (want 1)' % n
before = u.count('\n')
u2 = u.replace(anchor, repl)
assert u2.count(anchor) == 0, 'anchor still present after replace'
delta = u2.count('\n') - before
assert delta == len((doc + '\n' + code).split('\n')), 'delta mismatch %d' % delta
json.dump({'file': REL, 'anchor': anchor, 'repl': repl, 'count': 1},
          io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
print('wrote %s: anchor unique, inserting %d net lines' % (OUT, delta))

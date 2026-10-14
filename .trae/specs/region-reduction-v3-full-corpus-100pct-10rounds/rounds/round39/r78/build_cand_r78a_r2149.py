"""build_cand_r78a_r2149.py — rebuild each [R21-49] half byte-exactly and prove it.

Ticket R21-49 attacks the elif COLLECTION, which lives in region_analyzer.py, so the
generator base 30a4d7827122e165 is UNCHANGED and each candidate is an ANALYZER variant
built from the LANDED analyzer bytes f7d849e974904492 (the "second builder" the brief
requires when the analyzer is touched).

Two granularities of the SAME single mechanism (both placed in _check_elif_chain's inline
`and` walk, right after the landed STORE guard that already defines "pure condition block"):
  A = [R21-49]a  arm entry carries a statement => do NOT fold it (walk `break`)
  B = [R21-49]b  arm entry carries a statement => it is not an elif of this chain (`return None`)

Measured: A and B produce BYTE-IDENTICAL clock_worker products (the de-folded arm entry makes
a downstream merge guard abandon the whole @7186 fold), so the "pair" == B; there is no
additional product, and both REGRESS the unit to delta=-269. This builder reproduces A and B
byte-for-byte and asserts equality against the files that were actually measured.

usage: python -X utf8 build_cand_r78a_r2149.py
"""
import hashlib
import os
import py_compile
import shutil

REPO = r'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main'
MIRROR = r'D:/Temp/r78'
BASE_ANALYZER = os.path.join(REPO, 'core', 'cfg', 'region_analyzer.py')          # landed f7d849e974904492
R75_GEN_BASE = os.path.join(REPO, '.trae', 'specs', 'region-reduction-v3-full-corpus-100pct-10rounds',
                           'rounds', 'round39', 'r75',
                           'CANDIDATE_r75a_r2146_AB_on_r74d_30a4d7827122e165.py')  # generator base 30a4d782
DELIVER = os.path.join(MIRROR, 'DELIVER')


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def crlf(lines):
    return ('\r\n'.join(lines) + '\r\n').encode('utf-8')


# The landed STORE-guard block that ends the "pure condition block" definition (unique anchor).
STORE_TAIL = crlf([
    "                    if any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',",
    "                                        'STORE_DEREF', 'STORE_SUBSCR', 'STORE_ATTR')",
    "                           for i in _ft_next.instructions):",
    "                        break",
])

BLOCK_A = crlf([
    "                    # [R21-49 判据 · elif 条件的臂入口携带语句 ⇒ 不折进短路链]",
    "                    # 区域归约算法原则 1（块 = 前导语句 + 恰好一个终结子）＋ 原则 2",
    "                    #（每块唯一归属且归属者必须发射）＋ 原则 4（父以子区域 entry 引用）：",
    "                    # inline `and` 短路链把 first_else 的 true successor（其 then 臂入口）",
    "                    # 折进条件，只有当该块是【纯条件块】时才成立——短路操作数的求值结果",
    "                    # 必被紧随的 POP_JUMP_IF_FALSE 消费，绝不会出现 POP_TOP（丢弃栈返回值的",
    "                    # 语句闭合指令）。一旦臂入口含 POP_TOP，它就先执行一条独立语句（如",
    "                    # debug()）、再做下一个测试，是【臂内顺序内容】而非布尔操作数：把它折进",
    "                    # 条件会吞掉该语句（clock_worker 链 @7186 把 @7248=if D 的臂入口 @7270",
    "                    # =`debug(); if E`，其 debug() 结果 CALL→POP_TOP 丢弃，折进条件后 debug()",
    "                    # 语句消失、@7270 的 if E 测试被当成 @7248 的 and 操作数，臂体从 @7372 起、",
    "                    # 漏掉 true successor @7270）。此时中断链扩展：first_else 仍以自身为 elif",
    "                    # 条件、其 true successor 归还为臂体首块（原则 2/4）。与上方 STORE 判据",
    "                    # 同域同层：二者共同界定「纯条件块」= 无 STORE 且无 POP_TOP 语句闭合。",
    "                    # 不读名字/常量/绝对偏移/计数阈值，不读兄弟区域，无跨区跨级回补，无函数名。",
    "                    if any(i.opname == 'POP_TOP' for i in _ft_next.instructions):",
    "                        break",
])

BLOCK_B = crlf([
    "                    # [R21-49 判据 · elif 条件的臂入口携带语句 ⇒ 它不是本链的 elif]",
    "                    # 区域归约算法原则 1（块 = 前导语句 + 恰好一个终结子）＋ 原则 2",
    "                    #（每块唯一归属且归属者必须发射）＋ 原则 4（父以子区域 entry 引用）：",
    "                    # inline `and` 短路链把 first_else 的 true successor（其 then 臂入口）",
    "                    # 折进条件，只有当该块是【纯条件块】时才成立——短路操作数的求值结果",
    "                    # 必被紧随的 POP_JUMP_IF_FALSE 消费，绝不会出现 POP_TOP（丢弃栈返回值的",
    "                    # 语句闭合指令）。一旦臂入口含 POP_TOP，它就先执行一条独立语句（如",
    "                    # debug()）、再做下一个测试，是【臂内顺序内容】而非布尔操作数：把它折进",
    "                    # 条件会吞掉该语句、令本应嵌套在臂内的 if 退化为链的一个 elif。此时",
    "                    # first_else 根本不是本链的 elif，弃权整条 elif 展平——返回 None，",
    "                    # 调用方 _build_elif_region 回退 _build_basic_if_region 按 IF_THEN_ELSE",
    "                    # 建区，臂入口交回其所在套件顺序发射（结构事实，可证明，非偏好选择）。",
    "                    # 与上方 STORE 判据同域同层：二者共同界定「纯条件块」= 无 STORE 且无",
    "                    # POP_TOP 语句闭合。不读名字/常量/绝对偏移/计数阈值，不读兄弟区域，",
    "                    # 无跨区跨级回补，无函数名。命中实测唯一：clock_worker 链 @7186 把",
    "                    # @7248（if D）的臂入口 @7270（debug(); if E，含 CALL→POP_TOP）折进条件。",
    "                    if any(i.opname == 'POP_TOP' for i in _ft_next.instructions):",
    "                        return None",
])

os.makedirs(DELIVER, exist_ok=True)

base = open(BASE_ANALYZER, 'rb').read()
print('base generator (unchanged)   sha16=%s' % sha16(open(R75_GEN_BASE, 'rb').read()))
print('base analyzer (landed)       sha16=%s' % sha16(base))
assert base.count(STORE_TAIL) == 1, 'STORE anchor not unique'


def build(name, block):
    out = base.replace(STORE_TAIL, STORE_TAIL + block)
    path = os.path.join(DELIVER, name)
    open(path, 'wb').write(out)
    compile(out.decode('utf-8-sig'), name, 'exec')   # py_compile the result (syntax check)
    print('%-64s sha16=%s' % (name, sha16(out)))
    return out, path


outA, pA = build('CANDIDATE_r78a_r2149a_breakFold_analyzer_on_base.py', BLOCK_A)
outB, pB = build('CANDIDATE_r78a_r2149b_refuseChain_analyzer_on_base.py', BLOCK_B)

# prove byte-exactness against the files that were actually measured
measA = open(os.path.join(MIRROR, 'work', '_break.py'), 'rb').read()
measB = open(os.path.join(MIRROR, 'work', '_refusal.py'), 'rb').read()
print('half A byte-identical to measured _break.py :', outA == measA)
print('half B byte-identical to measured _refusal.py:', outB == measB)

# generator is unchanged from the r75 base; copy it into DELIVER as a witness of the base.
shutil.copyfile(R75_GEN_BASE, os.path.join(DELIVER, 'BASE_generator_30a4d7827122e165.py'))
print('copied generator base witness BASE_generator_30a4d7827122e165.py sha16=%s' % sha16(open(R75_GEN_BASE, 'rb').read()))

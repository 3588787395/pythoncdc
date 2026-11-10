# fix156_battery.py: r156_regress.py ensure/markers — v156 marker lives in CG
# (code_generator.py), not AC (ast_converter.py). Fix both ensure_v156 and the
# HEAD-side anti-contamination assert.
import io

P = r'F:/Downloads/pythoncdc-main/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/binparen/r156_regress.py'
s = io.open(P, encoding='utf-8').read()

old1 = """    b = open(RAG, 'rb').read()
    b2 = open(RAG2, 'rb').read()
    b3 = open(AC, 'rb').read()
    assert (b'v152-ORCLAIM' in b and b'v152-LATCH' in b
            and b'v155-CONDLEAK' in b
            and b'v153-RESIDUNPACK' in b2
            and b'v154-KWMERGE' in b3
            and b'v156-BINPAREN' in b3), \\
        'v156 markers missing — work tree not on v156, abort (no self-heal this round)'
    return b"""
assert s.count(old1) == 1, 'ensure anchor %d' % s.count(old1)
new1 = """    b = open(RAG, 'rb').read()
    b2 = open(RAG2, 'rb').read()
    b3 = open(AC, 'rb').read()
    b4 = open(CG, 'rb').read()
    assert (b'v152-ORCLAIM' in b and b'v152-LATCH' in b
            and b'v155-CONDLEAK' in b
            and b'v153-RESIDUNPACK' in b2
            and b'v154-KWMERGE' in b3
            and b'v156-BINPAREN' in b4), \\
        'v156 markers missing — work tree not on v156, abort (no self-heal this round)'
    return b"""
s = s.replace(old1, new1, 1)

old2 = """    assert b'v156-BINPAREN' not in head_rag, 'HEAD already contains v156 patch?'
    assert b'v152-ORCLAIM' in head_rag, 'HEAD analyzer should contain v152 patch'"""
assert s.count(old2) == 1, 'head anchor %d' % s.count(old2)
new2 = """    head_cg = subprocess.run([GIT, '-C', REPO, 'show', HEAD + ':core/cfg/code_generator.py'],
                             capture_output=True).stdout
    assert b'v156-BINPAREN' not in head_cg, 'HEAD already contains v156 patch?'
    assert b'v152-ORCLAIM' in head_rag, 'HEAD analyzer should contain v152 patch'"""
s = s.replace(old2, new2, 1)

io.open(P, 'w', encoding='utf-8').write(s)
import py_compile
py_compile.compile(P, doraise=True)
print('battery markers fixed, syntax OK')

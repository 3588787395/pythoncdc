# PATCH_R21-81_region_ast_generator.py
# Idempotent absolute-path anchored edit of region_ast_generator.py:
#   base 566ff5c502276e48  ->  R21-81 candidate.
# The candidate makes the if-arm scanner dispatch nested-region entries that sit inside the
# parent region's body block list, which the generated_blocks gate currently swallows whole.
# Asserted after write: BOM preserved, zero bare LF, zero CR CR LF, py_compile passes.
import hashlib
import subprocess
import sys

TARGET = r'D:/Temp/r108/core/cfg/region_ast_generator.py'
BASE_SHA16 = '566ff5c502276e48'
BOM = b'\xef\xbb\xbf'

HELPER = [
    '    def _r2181_note_emitted(self, region, ast_result) -> None:',
    '        """[R21-81] Record that a structural region actually produced source.',
    '',
    '        Principle 2 (unique block membership) is tracked by two independent ledgers:',
    '        `generated_blocks` (a block was CONSUMED by some emission path - including the',
    '        walks that flatten a member block into ordinary statements) and',
    '        `_generated_regions` (a region was DISPATCHED, written by only some paths).',
    '        A block that is the entry of a nested region can therefore sit in',
    '        `generated_blocks` while its region has never been emitted, and the arm scan',
    '        then refuses the very dispatch it registered itself, so the entry and its whole',
    '        statement run disappear.  This helper is the missing third ledger, written at',
    '        the single central dispatch funnel `_generate_region` - the only place that',
    '        knows a region became source.  It stores the region ENTRY BLOCK when the funnel',
    '        returned a non-empty result.  Region data only: no names, no offsets as keys,',
    '        no counters, no thresholds.',
    '        """',
    '        if not ast_result:',
    '            return',
    "        entry = getattr(region, 'entry', None)",
    '        if entry is None:',
    '            return',
    "        emitted = getattr(self, '_r2181_emitted_entries', None)",
    '        if emitted is None:',
    '            emitted = self._r2181_emitted_entries = set()',
    '        emitted.add(entry)',
    '',
    '    def _r2181_region_entry_emitted(self, region) -> bool:',
    '        """[R21-81] True iff the funnel already turned `region` into source."""',
    "        entry = getattr(region, 'entry', None)",
    '        if entry is None:',
    '            return False',
    "        emitted = getattr(self, '_r2181_emitted_entries', None)",
    '        return emitted is not None and entry in emitted',
    '',
]

EVA = [
    '        self._generating_regions: Set[int] = set()',
    '        self._generated_regions: Set[int] = set()',
]
EVB = EVA + [
    '        # [R21-81] third ownership ledger: entry blocks of regions the central',
    '        # dispatch funnel has already turned into source statements.',
    "        self._r2181_emitted_entries: Set[Any] = set()",
]

GATE = [
    '            if block in self.generated_blocks:',
    '                continue',
    '            # [F-GET_ITER fix] Skip blocks that are for_iter_setup of a',
]
GATED = [
    '            # [R21-81] Block consumption and region emission are different facts.',
    '            # An entry this arm has itself registered as a nested-region dispatch',
    '            # target is dispatched even when `generated_blocks` already holds it',
    '            # (principles 2 and 4: the parent references the child only through its',
    '            # entry, and the child must be emitted exactly once).  A registered entry',
    '            # whose region the central funnel has already emitted keeps the original',
    '            # skip, so nothing is ever printed twice; unregistered blocks are',
    '            # untouched and behaviour is byte-identical.',
    '            if block in self.generated_blocks:',
    '                _r2181_target = None',
    '                if block in _nested_if_entry_generate:',
    '                    _r2181_target = _nested_if_entry_generate[block]',
    '                elif block in _try_entry_generate:',
    '                    _r2181_target = _try_entry_generate[block]',
    '                elif block in _loop_entry_generate:',
    '                    _r2181_target = _loop_entry_generate[block]',
    '                elif block in _r2_b107_child_generate:',
    '                    _r2181_target = _r2_b107_child_generate[block][0]',
    '                if (_r2181_target is None',
    '                        or self._r2181_region_entry_emitted(_r2181_target)):',
    '                    continue',
    '            # [F-GET_ITER fix] Skip blocks that are for_iter_setup of a',
]

FUNNELS = [
    (['            return self._generate_loop(region, skip_store_targets=skip_store_targets)'],
     ['            _r2181_loop_ast = self._generate_loop(',
      '                region, skip_store_targets=skip_store_targets)',
      '            # [R21-81] funnel ledger: the loop region produced source here.',
      '            self._r2181_note_emitted(region, _r2181_loop_ast)',
      '            return _r2181_loop_ast'], 'loop-funnel'),
    (['                return None',
      '            return self._generate_if(region)'],
     ['                return None',
      '            _r2181_if_ast = self._generate_if(region)',
      '            # [R21-81] funnel ledger: the if region produced source here.',
      '            self._r2181_note_emitted(region, _r2181_if_ast)',
      '            return _r2181_if_ast'], 'if-funnel'),
    (['            return self._generate_try(region)'],
     ['            _r2181_try_ast = self._generate_try(region)',
      '            # [R21-81] funnel ledger: the try region produced source here.',
      '            self._r2181_note_emitted(region, _r2181_try_ast)',
      '            return _r2181_try_ast'], 'try-funnel'),
    (['            return self._generate_with(region)'],
     ['            _r2181_with_ast = self._generate_with(region)',
      '            # [R21-81] funnel ledger: the with region produced source here.',
      '            self._r2181_note_emitted(region, _r2181_with_ast)',
      '            return _r2181_with_ast'], 'with-funnel'),
    (['            return self._generate_match(region)'],
     ['            _r2181_match_ast = self._generate_match(region)',
      '            # [R21-81] funnel ledger: the match region produced source here.',
      '            self._r2181_note_emitted(region, _r2181_match_ast)',
      '            return _r2181_match_ast'], 'match-funnel'),
]


def find_all(lines, block):
    n = len(block)
    return [i for i in range(len(lines) - n + 1) if lines[i:i + n] == block]


def replace_unique(lines, block, repl, tag):
    hits = find_all(lines, block)
    if find_all(lines, repl):
        return tag + '(already)'
    if len(hits) == 1:
        lines[hits[0]:hits[0] + len(block)] = repl
        return tag
    if len(hits) == 0:
        raise SystemExit('ANCHOR MISSING: %s' % tag)
    raise SystemExit('ANCHOR AMBIGUOUS: %s %s' % (tag, hits))


def apply_once(lines):
    applied = []
    applied.append(replace_unique(lines, EVA, EVB, 'registry-field'))

    helper_anchor = '    def _generate_region(self, region: Region, skip_store_targets: Set[str] = None)'
    idx = [i for i, ln in enumerate(lines) if ln.startswith(helper_anchor)]
    if len(idx) != 1:
        raise SystemExit('FUNNEL ANCHOR BAD: %s' % idx)
    if any('_r2181_note_emitted(self' in ln for ln in lines):
        applied.append('helpers(already)')
    else:
        lines[idx[0]:idx[0]] = list(HELPER)
        applied.append('helpers')

    applied.append(replace_unique(lines, GATE, GATED, 'arm-gate'))
    for block, repl, tag in FUNNELS:
        applied.append(replace_unique(lines, block, repl, tag))
    return applied


def main():
    raw = open(TARGET, 'rb').read()
    bom = raw.startswith(BOM)
    before = hashlib.sha256(raw).hexdigest()[:16]
    lines = raw.decode('utf-8-sig').split('\r\n')
    applied = apply_once(lines)
    out = '\r\n'.join(lines).encode('utf-8')
    if bom:
        out = BOM + out
    assert out.count(b'\r\r\n') == 0, 'CR CR LF corruption'
    assert out.count(b'\n') - out.count(b'\r\n') == 0, 'bare LF introduced'
    assert out.startswith(BOM), 'BOM lost'
    open(TARGET, 'wb').write(out)
    assert open(TARGET, 'rb').read() == out, 'write-back mismatch'
    assert subprocess.run([sys.executable, '-X', 'utf8', '-m', 'py_compile',
                           TARGET]).returncode == 0, 'py_compile failed'
    print('[R21-81] base sha16=%s applied=%s' % (before, applied))
    print('[R21-81] bytes=%d sha16=%s crlf=%d bareLF=%d crCRCR=%d bom=%s' % (
        len(out), hashlib.sha256(out).hexdigest()[:16], out.count(b'\r\n'),
        out.count(b'\n') - out.count(b'\r\n'), out.count(b'\r\r\n'), out.startswith(BOM)))


main()

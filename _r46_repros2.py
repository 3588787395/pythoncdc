"""R46 test engineer: Create minimal repros for the most common defect patterns."""
import sys, os, py_compile, marshal, types, dis
sys.path.insert(0, '.')
from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode

REPRO_DIR = ".trae/specs/region-comment-multi-pyc-iteration/rounds/round_46/test_engineer/minimal_repros"
os.makedirs(REPRO_DIR, exist_ok=True)

def extract_code_objects(code_obj, prefix=''):
    result = {}
    name = prefix + code_obj.co_name if prefix else (code_obj.co_name or '<module>')
    result[name] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            child_prefix = (prefix + code_obj.co_name + ".") if prefix else (code_obj.co_name + ".")
            result.update(extract_code_objects(const, child_prefix))
    return result

def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def test_repro(name, source):
    py_path = os.path.join(REPRO_DIR, f"{name}.py")
    pyc_path = os.path.join(REPRO_DIR, f"{name}.pyc")
    ok_path = os.path.join(REPRO_DIR, f"{name}OK.py")
    with open(py_path, 'w', encoding='utf-8') as f:
        f.write(source)
    try:
        py_compile.compile(str(py_path), str(pyc_path), doraise=True)
    except Exception as e:
        return False, f"COMPILE_ERR: {e}"
    try:
        orig_code = load_pyc_code(str(pyc_path))
    except Exception as e:
        return False, f"LOAD_ERR: {e}"
    try:
        decomp_source = decompile_pyc(str(pyc_path))
        if decomp_source is None:
            return False, "DECOMPILE_NULL"
        with open(ok_path, 'w', encoding='utf-8') as f:
            f.write(decomp_source)
    except Exception as e:
        return False, f"DECOMPILE_ERR: {e}"
    try:
        cfile = py_compile.compile(str(ok_path), doraise=True, quiet=2)
        with open(cfile, 'rb') as f:
            f.read(16)
            decomp_code = marshal.load(f)
    except Exception as e:
        return True, f"RECOMPILE_ERR: {e}"
    orig_map = extract_code_objects(orig_code)
    decomp_map = extract_code_objects(decomp_code)
    common = set(orig_map.keys()) & set(decomp_map.keys())
    total = len(orig_map)
    matched = 0
    first_diff = None
    for func_name in sorted(common):
        cmp = compare_bytecode(orig_map[func_name], decomp_map[func_name])
        if cmp.get('match') or cmp.get('jump_only'):
            matched += 1
        elif first_diff is None:
            true_diffs = cmp.get('true_diffs', [])
            if true_diffs:
                td = true_diffs[0]
                first_diff = f"{td.get('orig_op','?')}({td.get('orig_arg','?')}) -> {td.get('decomp_op','?')}({td.get('decomp_arg','?')})"
            else:
                first_diff = "jump_only_diff"
    defect = matched < total
    return defect, f"{matched}/{total} matched" + (f", first_diff: {first_diff}" if first_diff else "")

repros = [
    # Pattern 1: or expression with COPY + chained STORE (from load_from_kwargs)
    ("repro_13_or_copy_store",
     'def func(x, y):\n'
     '    a = None\n'
     '    if y > 0:\n'
     '        a = a or x.get(y).close\n'
     '        b = a\n'
     '    return b\n'),
    ("repro_14_or_copy_store_simple",
     'def func(x):\n'
     '    a = None\n'
     '    a = a or x.close\n'
     '    b = a\n'
     '    return b\n'),
    ("repro_15_or_assign_chain",
     'def func(x, y):\n'
     '    a = None\n'
     '    if y:\n'
     '        a = a or x.get(y)\n'
     '        b = a\n'
     '    return b\n'),
    # Pattern 2: Nested if in then branch with elif (from make_trade)
    ("repro_16_nested_if_elif",
     'class Foo:\n'
     '    def func(self, x):\n'
     '        if x.dir == 1:\n'
     '            if x.sub == 0:\n'
     '                self.a = 1\n'
     '                return -1\n'
     '            else:\n'
     '                self.a = 2\n'
     '        elif x.dir == 2:\n'
     '            self.a = 3\n'
     '            return 4\n'
     '        return 0\n'),
    ("repro_17_nested_if_else",
     'class Foo:\n'
     '    def func(self, x):\n'
     '        if x.dir == 1:\n'
     '            if x.sub == 0:\n'
     '                return 1\n'
     '            else:\n'
     '                return 2\n'
     '        else:\n'
     '            return 3\n'),
    ("repro_18_nested_if_no_else",
     'class Foo:\n'
     '    def func(self, x):\n'
     '        if x.dir == 1:\n'
     '            if x.sub == 0:\n'
     '                self.a = 1\n'
     '                return -1\n'
     '            else:\n'
     '                self.a = 2\n'
     '        else:\n'
     '            self.a = 3\n'
     '            return 4\n'),
    # Pattern 3: for-else with continue (from load_from_kwargs)
    ("repro_19_for_else_continue",
     'def func(kwargs):\n'
     '    new_kwargs = {}\n'
     '    for side in ("sell", "buy"):\n'
     '        avg = 0\n'
     '        for key in ("_old", "_today"):\n'
     '            key = side + key\n'
     '            amount = int(kwargs.get(key + "_amount", 0))\n'
     '            if amount > 0:\n'
     '                price = float(kwargs.get(key + "_price", 0))\n'
     '                if price <= 0:\n'
     '                    price = 0\n'
     '                avg = (avg + price) / 2 if avg else price\n'
     '            continue\n'
     '        new_kwargs[side + "_avg"] = avg\n'
     '    else:\n'
     '        if new_kwargs:\n'
     '            return new_kwargs\n'
     '        else:\n'
     '            raise ValueError("error")\n'),
    ("repro_20_for_else_simple",
     'def func(items):\n'
     '    result = {}\n'
     '    for item in items:\n'
     '        val = int(item)\n'
     '        if val > 0:\n'
     '            result[item] = val\n'
     '        continue\n'
     '    else:\n'
     '        if result:\n'
     '            return result\n'
     '        raise ValueError("empty")\n'),
    # Pattern 4: PUSH_EXC_INFO handling (from logger)
    ("repro_21_try_except_format",
     'def func(self, record):\n'
     '    try:\n'
     '        msg = record.getMessage()\n'
     '    except Exception:\n'
     '        msg = repr(record)\n'
     '    return msg\n'),
    ("repro_22_push_exc_info",
     'def func(exc):\n'
     '    try:\n'
     '        return str(exc)\n'
     '    except Exception:\n'
     '        return "error"\n'),
    # Pattern 5: COPY with STORE for augmented assignment
    ("repro_23_copy_store_aug",
     'class Foo:\n'
     '    def func(self):\n'
     '        self.a += 1\n'
     '        self.b = self.a\n'
     '        return self.b\n'),
    # Pattern 6: Multiple nested if with return in each branch
    ("repro_24_nested_if_return",
     'class Foo:\n'
     '    def make_trade(self, trade):\n'
     '        amount = trade.amount\n'
     '        if trade.direction == 1:\n'
     '            if trade.sub == 0:\n'
     '                if self.count == 0:\n'
     '                    self.time = trade.date\n'
     '                self.type = 1\n'
     '                self.avg = (self.avg * self.count + amount * trade.price) / (self.count + amount)\n'
     '                self.cost += trade.cost\n'
     '                self.list.insert(0, (trade.price, amount))\n'
     '                return -1\n'
     '            else:\n'
     '                if self.count - amount != 0:\n'
     '                    self.avg = (self.avg * self.count - amount * trade.price) / (self.count - amount)\n'
     '                else:\n'
     '                    old = self.val\n'
     '                    self.cost += trade.cost\n'
     '                    delta = self.close(trade)\n'
     '                    self.pnl += delta\n'
     '                    return old - self.val + delta\n'
     '        else:\n'
     '            if trade.sub == 0:\n'
     '                if self.count2 == 0:\n'
     '                    self.time2 = trade.date\n'
     '                self.type = 2\n'
     '                self.avg2 = (self.avg2 * self.count2 + amount * trade.price) / (self.count2 + amount)\n'
     '                self.cost2 += trade.cost\n'
     '                self.list2.insert(0, (trade.price, amount))\n'
     '                return -1\n'
     '            else:\n'
     '                if self.count2 - amount != 0:\n'
     '                    self.avg2 = (self.avg2 * self.count2 - amount * trade.price) / (self.count2 - amount)\n'
     '                else:\n'
     '                    self.time2 = trade.date\n'
     '                    self.avg2 = 0.0\n'
     '                old = self.val\n'
     '                self.cost2 += trade.cost\n'
     '                delta = self.close(trade)\n'
     '                self.pnl2 += delta\n'
     '                return old - self.val + delta\n'),
]

results = []
for name, source in repros:
    defect, details = test_repro(name, source)
    status = "DEFECT-REPRO" if defect else "NO-DEFECT"
    results.append((name, status, details))
    print(f"  {name:40s}  {status:15s}  {details}")

defects = [r for r in results if r[1] == "DEFECT-REPRO"]
print(f"\n=== Summary ===")
print(f"Total repros: {len(results)}")
print(f"DEFECT-REPRO: {len(defects)}")
print(f"NO-DEFECT: {len(results) - len(defects)}")

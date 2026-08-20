import dis, marshal, sys, types

f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
f.close()

for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'exception_handling_complex':
        lines = []
        lines.append(f"=== {c.co_name} ===")
        lines.append(f"argcount={c.co_argcount}, varnames={c.co_varnames}")
        lines.append(f"consts count={len(c.co_consts)}")
        for i, const in enumerate(c.co_consts):
            if hasattr(const, 'co_name'):
                lines.append(f"  const[{i}]: <code {const.co_name}>")
            else:
                lines.append(f"  const[{i}]: {repr(const)}")
        lines.append("")
        lines.append("=== Instructions ===")
        for inst in dis.get_instructions(c):
            lines.append(f"  {inst.offset:4d} {inst.opname:30s} {inst.argrepr}")
        lines.append("")
        lines.append("=== Exception Table ===")
        try:
            et = dis.ExceptionTable.from_bytes(c.co_exceptiontable)
            for entry in et:
                lines.append(f"  start={entry.start}, end={entry.end}, target={entry.target}, depth={entry.depth}, lasti={entry.lasti}")
        except Exception as e:
            lines.append(f"  Error: {e}")
        
        with open('_r109_ehc_orig.txt', 'w', encoding='utf-8') as outf:
            outf.write('\n'.join(lines))
        print("Done")
        break

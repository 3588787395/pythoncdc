# -*- coding: utf-8 -*-
"""Round 35 synthetic shapes (G0).  Corpus-free names; every shape is a single function.

Each entry carries two sources that differ by exactly one handler-tail `return None` statement,
so the runner can first ask the compiler-side question: is that source-level choice visible in
the bytecode at all?  If not, the shape witnesses nothing (reported UNDERDETERMINED).

r35_01  WITNESS      three nested try/except, innermost handler falls out of the function.
                     Target shape (`save_testds_to_json`): the landed core fabricates
                     `return None` there and loses 4 instructions.
r35_02  CONTROL      single handler with a real handler-tail return.
r35_03  CONTROL      two nested handlers plus code after the try statement: the tail return is
                     materialised and required.
r35_04  CONTROL      two nested handlers, innermost falls out at handler depth 2 (where the
                     compiler emits the same bytes for both choices).
r35_05  NEGATIVE     innermost handler tail has a REAL `return None` at depth 3, i.e. the code
                     object genuinely holds several cleanup epilogues and the tail one must be
                     emitted.  This is the shape that falsifies a predicate keyed on
                     "duplicate epilogue exists" alone.
"""

SHAPES = {}

SHAPES['r35_01_witness_dup_epilogue_fallthrough'] = {
    'src': """def store(payload):
    try:
        payload.write()
        return None
    except BaseException:
        print('write failed')
        try:
            payload.dump()
            return None
        except BaseException:
            print('dump failed')
            try:
                payload.text()
            except BaseException:
                print('text failed')
""",
    'alt': """def store(payload):
    try:
        payload.write()
        return None
    except BaseException:
        print('write failed')
        try:
            payload.dump()
            return None
        except BaseException:
            print('dump failed')
            try:
                payload.text()
            except BaseException:
                print('text failed')
                return None
""",
}

SHAPES['r35_02_control_single_epilogue'] = {
    'src': """def store(payload):
    try:
        payload.write()
    except BaseException:
        print('write failed')
        return None
""",
    'alt': """def store(payload):
    try:
        payload.write()
    except BaseException:
        print('write failed')
""",
}

SHAPES['r35_03_control_trailing_code'] = {
    'src': """def store(payload):
    try:
        payload.write()
    except BaseException:
        print('write failed')
        try:
            payload.dump()
        except BaseException:
            print('dump failed')
            return None
    print('done')
""",
    'alt': """def store(payload):
    try:
        payload.write()
    except BaseException:
        print('write failed')
        try:
            payload.dump()
        except BaseException:
            print('dump failed')
    print('done')
""",
}

SHAPES['r35_04_control_depth2_fallout'] = {
    'src': """def store(payload):
    try:
        payload.write()
        return None
    except BaseException:
        print('write failed')
        try:
            payload.dump()
        except BaseException:
            print('dump failed')
""",
    'alt': """def store(payload):
    try:
        payload.write()
        return None
    except BaseException:
        print('write failed')
        try:
            payload.dump()
        except BaseException:
            print('dump failed')
            return None
""",
}

SHAPES['r35_05_negative_real_return_at_depth3'] = {
    'src': """def store(payload):
    try:
        payload.write()
        return None
    except BaseException:
        print('write failed')
        try:
            payload.dump()
            return None
        except BaseException:
            print('dump failed')
            try:
                payload.text()
            except BaseException:
                print('text failed')
                return None
""",
    'alt': """def store(payload):
    try:
        payload.write()
        return None
    except BaseException:
        print('write failed')
        try:
            payload.dump()
            return None
        except BaseException:
            print('dump failed')
            try:
                payload.text()
            except BaseException:
                print('text failed')
""",
}

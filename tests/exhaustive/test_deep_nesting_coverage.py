#!/usr/bin/env python3
"""
四层及更深嵌套测试 - 深层控制流嵌套完备性验证

覆盖4层至8层的控制流嵌套，检验反编译器对深层嵌套的处理能力。
重点测试区域归约算法在深度递归下的正确性和稳定性。

理论依据（编译器结构化分析理论）：
- 区域归约是自底向上的迭代过程（Johnson et al. 1994）
- 深层嵌套产生高阶支配关系和复杂的回边模式
- 算法复杂度随嵌套深度线性增长（O(N) where N = basic blocks）

测试矩阵：
| ID | 层数 | 结构 | 说明 |
|----|------|------|------|
| Q01-Q20 | 4层 | 基础四层嵌套 | 各类四层排列组合 |
| Q21-Q35 | 5层 | 五层混合嵌套 | 五种结构的五层组合 |
| Q36-Q45 | 6-8层 | 极限深度嵌套 | 压力测试 |
| Q46-Q55 | 特殊场景 | 控制转移/复合条件 | break/continue/return/raise在深层中 |
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.helpers.decompilation_helper import MatrixTestBase


class TestDeepNestingCoverage(MatrixTestBase):
    """四层及以上控制流嵌套完备性测试 - 覆盖55个深层嵌套场景"""

    # ========================================================================
    # Q01-Q20: 四层基础嵌套 (4-level basic nesting)
    # ========================================================================

    def test_Q01_for_if_for_if(self):
        """Q01: for>if>for>if - 交替嵌套：循环>条件>循环>条件

        四层交替嵌套模式，最常见的实际代码模式。
        测试要点：双层for-if的独立作用域、内层if不影响外层for"""
        source = '''
def func(data):
    results = []
    for i in range(len(data)):
        if data[i] > 0:
            for j in range(i + 1, len(data)):
                if data[j] > data[i]:
                    results.append((i, j))
    return results
'''
        self.verify_matrix_decompilation(source, 'Q01')

    def test_Q02_while_try_while_if(self):
        """Q02: while>try>while>if - 同类型间隔嵌套

        外层while和内层while之间隔了try块。
        测试要点：两个while的回边不混淆、try正确包裹内层while+if"""
        source = '''
def func(processor):
    while processor.active():
        try:
            processor.prepare()
            sub = processor.subprocess()
            while sub.running():
                if sub.has_output():
                    collect(sub.get_output())
        except ProcessError:
            processor.recover()
'''
        self.verify_matrix_decompilation(source, 'Q02')

    def test_Q03_if_for_try_except(self):
        """Q03: if>for>try>except - 条件>循环>异常处理

        标准的四层业务逻辑模式。
        测试要点：except只捕获for体内的异常、不影响外层if"""
        source = '''
def func(enabled, items):
    if enabled:
        for item in items:
            try:
                result = process(item)
                save(result)
            except ProcessError as e:
                log_error(e, item)
'''
        self.verify_matrix_decompilation(source, 'Q03')

    def test_Q04_try_for_if_while(self):
        """Q04: try>for>if>while - 异常保护>循环>条件>循环

        异常保护包裹三层嵌套。
        测试要点：最内层while的break不影响中间for"""
        source = '''
def func(source):
    try:
        batches = source.read_batches()
        for batch in batches:
            if batch.is_valid():
                cursor = batch.cursor()
                while cursor.has_next():
                    record = cursor.next()
                    emit(record)
    except SourceError as e:
        handle_source_error(e)
'''
        self.verify_matrix_decompilation(source, 'Q04')

    def test_Q05_for_while_if_try(self):
        """Q05: for>while>if>try - 双层循环>条件>异常保护

        五层的前奏，双层异构循环加条件再加异常。
        测试要点：try的范围精确到if内部"""
        source = '''
def func(groups):
    for group in groups:
        iterator = group.iterator()
        while iterator.has_more():
            item = iterator.next()
            if item.needs_processing():
                try:
                    processed = transform(item)
                    output(processed)
                except TransformError:
                    output_default(item)
'''
        self.verify_matrix_decompilation(source, 'Q05')

    def test_Q06_while_if_for_try(self):
        """Q06: while>if>for>try - 条件循环>条件>迭代>异常"""
        source = '''
def func(server):
    while server.is_connected():
        request = server.receive()
        if request:
            for part in request.parts():
                try:
                    handle(part)
                except HandleError:
                    skip_part(part)
'''
        self.verify_matrix_decompilation(source, 'Q06')

    def test_Q07_if_try_for_while(self):
        """Q07: if>try>for>while - 条件>异常>迭代>条件循环"""
        source = '''
def func(mode, data):
    if mode == "full":
        try:
            tables = data.tables()
            for table in tables:
                reader = table.reader()
                while reader.has_row():
                    row = reader.read_row()
                    process(row)
        except DataError:
            fallback_process(data)
'''
        self.verify_matrix_decompilation(source, 'Q07')

    def test_Q08_for_if_for_if_for_if(self):
        """Q08: for>if>for>if>for>if - 同类型六层交替(3组for-if)

        同类型结构的重复嵌套模式。
        测试要点：三组for-if各自独立、缩进层次保持正确"""
        source = '''
def func(matrix):
    count = 0
    for i in range(len(matrix)):
        if matrix[i]:
            for j in range(len(matrix[i])):
                if matrix[i][j]:
                    for k in range(len(matrix[i][j])):
                        if matrix[i][j][k]:
                            count += 1
    return count
'''
        self.verify_matrix_decompilation(source, 'Q08', min_equivalence=0.80)

    def test_Q09_nested_break_in_deep_if(self):
        """Q09: 深层嵌套中的break - for>if>while>break

        控制转移语句在四层嵌套中的语义正确性。
        测试要点：break退出的是最近的for而不是while"""
        source = '''
def func(items):
    result = None
    for item in items:
        if item.searchable():
            subitems = item.children()
            idx = 0
            while idx < len(subitems):
                if subitems[idx].found():
                    result = subitems[idx]
                    break
                idx += 1
            if result:
                break
    return result
'''
        self.verify_matrix_decompilation(source, 'Q09')

    def test_Q10_nested_continue_in_deep_loop(self):
        """Q10: 深层嵌套中的continue - while>for>if>continue

        continue在多层嵌套中的目标循环正确性。"""
        source = '''
def func(pool):
    results = []
    while pool.has_tasks():
        batch = pool.get_batch()
        for task in batch:
            if task.skipped():
                continue
            try:
                result = execute(task)
                results.append(result)
            except TaskError:
                continue
    return results
'''
        self.verify_matrix_decompilation(source, 'Q10')

    def test_Q11_return_in_deep_nesting(self):
        """Q11: 深层嵌套中的return - if>for>try>return

        return从深层嵌套直接返回的正确性。"""
        source = '''
def func(items, target):
    for item in items:
        if item.matches(target):
            try:
                result = item.deep_extract()
                return result
            except ExtractError:
                return None
    return NOT_FOUND
'''
        self.verify_matrix_decompilation(source, 'Q11')

    def test_Q12_raise_in_deep_except(self):
        """Q12: 深层嵌套中的raise - for>try>except>raise

        异常重新抛出在深层嵌套中的传播路径。"""
        source = '''
def func(records):
    errors = []
    for rec in records:
        try:
            validate(rec)
            store(rec)
        except ValidationError as e:
            if e.fatal():
                raise
            errors.append(e)
    return errors
'''
        self.verify_matrix_decompilation(source, 'Q12')

    def test_Q13_complex_control_flow_combo(self):
        """Q13: 复杂控制流组合 - if>for>if>break + else

        多种控制转移的组合使用。"""
        source = '''
def func(data, threshold):
    found = False
    if data:
        for item in data:
            if item.value > threshold:
                found = True
                use(item)
                break
        else:
            found = False
    return found
'''
        self.verify_matrix_decompilation(source, 'Q13')

    @pytest.mark.slow
    def test_Q14_6level_limit_mixed(self):
        """Q14: 六层极限混合嵌套 - for>if>while>try>for>if

        六层混合嵌套的压力测试。
        测试要点：区域归约算法在6层深度下仍能正确工作"""
        source = '''
def func(data):
    results = []
    for i in range(3):
        if i > 0:
            j = 0
            while j < len(data[i]):
                try:
                    for k in range(2):
                        if k == data[i][j]:
                            results.append(k * i)
                except IndexError:
                    pass
                j += 1
    return results
'''
        self.verify_matrix_decompilation(source, 'Q14', min_equivalence=0.78)

    @pytest.mark.slow
    def test_Q15_7level_mixed_nesting(self):
        """Q15: 七层极限混合嵌套 - if>for>while>if>for>try>if

        七层嵌套极限测试。"""
        source = '''
def func(flag, matrix):
    if flag:
        for row in matrix:
            col = 0
            while col < len(row):
                if row[col] > 0:
                    for delta in range(3):
                        try:
                            val = compute(row[col], delta)
                            if val > 0:
                                results.append(val)
                        except ComputeError:
                            pass
                col += 1
'''
        self.verify_matrix_decompilation(source, 'Q15', min_equivalence=0.75)

    @pytest.mark.slow
    def test_Q16_8level_same_type_for(self):
        """Q16: 八层同类型(for)嵌套极限 - 纯for循环8层

        同类型深层嵌套极限压力测试。
        测试要点：8层纯for嵌套的区域识别能力"""
        source = '''
def func():
    count = 0
    for i1 in range(2):
        for i2 in range(2):
            for i3 in range(2):
                for i4 in range(2):
                    for i5 in range(2):
                        for i6 in range(2):
                            for i7 in range(2):
                                for i8 in range(2):
                                    count += 1
    return count
'''
        self.verify_matrix_decompilation(source, 'Q16', min_equivalence=0.75)

    def test_Q17_complex_body_deep_nesting(self):
        """Q17: 深层嵌套+复杂体 - 每层含多语句

        深层嵌套且每层包含多个语句的复杂场景。"""
        source = '''
def func(data):
    output = []
    for category in data.categories():
        if category.active():
            items = category.items()
            idx = 0
            while idx < len(items):
                item = items[idx]
                try:
                    validated = validate_item(item)
                    formatted = format_item(validated)
                    output.append(formatted)
                except ValidationError:
                    output.append(default_format(item))
                idx += 1
    return output
'''
        self.verify_matrix_decompilation(source, 'Q17')

    def test_Q18_compound_condition_deep(self):
        """Q18: 深层嵌套+复合条件 - and/or在深层if中

        复合布尔表达式在深层嵌套中的处理。"""
        source = '''
def func(config, data):
    results = []
    for entry in data:
        if entry.enabled and entry.valid:
            parts = entry.parts()
            i = 0
            while i < len(parts):
                part = parts[i]
                if (part.ready or part.forced) and not part.skip:
                    try:
                        result = execute_part(part)
                        results.append(result)
                    except ExecutionError:
                        results.append(None)
                i += 1
    return results
'''
        self.verify_matrix_decompilation(source, 'Q18')

    def test_Q19_exception_chaining_deep(self):
        """Q19: 深层嵌套+异常链 - 多层try-except嵌套

        异常处理在深层嵌套中的链式传播。"""
        source = '''
def func(request):
    try:
        session = create_session()
        try:
            user = authenticate(session)
            try:
                data = fetch_data(user)
                for record in data.records():
                    if record.complete():
                        try:
                            process(record)
                        except ProcessError:
                            record.mark_failed()
            except DataError:
                raise AuthError("data fetch failed") from None
        except AuthError:
            session.log_failure()
            raise
    except SessionError:
        return ERROR_RESPONSE
'''
        self.verify_matrix_decompilation(source, 'Q19')

    def test_Q20_with_chain_deep(self):
        """Q20: 深层with链 - with>with>if>for

        多层上下文管理器嵌套。"""
        source = '''
def func(db_path, cache_path):
    with open_db(db_path) as db:
        with open_cache(cache_path) as cache:
            if db.connected() and cache.ready():
                keys = db.all_keys()
                for key in keys:
                    value = db.get(key)
                    cache.set(key, value)
'''
        self.verify_matrix_decompilation(source, 'Q20')

    # ========================================================================
    # Q21-Q35: 五层混合嵌套 (5-level mixed nesting)
    # ========================================================================

    def test_Q21_five_level_if_for_while_if_for(self):
        """Q21: if>for>while>if>for - 五层标准混合"""
        source = '''
def func(mode, data):
    if mode == "process":
        for batch in data.batches():
            ptr = 0
            while ptr < len(batch):
                item = batch[ptr]
                if item.valid():
                    for sub in item.sub_items():
                        handle(sub)
                ptr += 1
'''
        self.verify_matrix_decompilation(source, 'Q21')

    def test_Q22_five_level_for_if_try_for_while(self):
        """Q22: for>if>try>for>while - 含异常保护的五层"""
        source = '''
def func(tasks):
    for task_group in tasks:
        if task_group.active():
            try:
                members = task_group.members()
                for member in members:
                    retries = 0
                    while retries < 3:
                        execute(member)
                        retries += 1
            except GroupError:
                skip_group(task_group)
'''
        self.verify_matrix_decompilation(source, 'Q22')

    def test_Q23_five_level_while_for_if_try_except(self):
        """Q23: while>for>if>try>except - 循环主导的五层"""
        source = '''
def func(worker):
    while worker.alive():
        jobs = worker.pending_jobs()
        for job in jobs:
            if job.priority >= HIGH:
                try:
                    run_job(job)
                except JobError as e:
                    if e.retryable():
                        job.reschedule()
                    else:
                        job.fail(e)
'''
        self.verify_matrix_decompilation(source, 'Q23')

    def test_Q24_five_level_try_for_while_if_for(self):
        """Q24: try>for>while>if>for - 异常包裹的五层"""
        source = '''
def func(dataset):
    try:
        tables = dataset.tables()
        for table in tables:
            reader = table.open_reader()
            while reader.has_row():
                row = reader.read_row()
                if row.not_empty():
                    for cell in row.cells():
                        process_cell(cell)
    except DatasetError:
        report_error(dataset)
'''
        self.verify_matrix_decompilation(source, 'Q24')

    def test_Q25_five_level_if_while_for_try_while(self):
        """Q25: if>while>for>try>while - 双while五层"""
        source = '''
def func(enabled, source):
    if enabled:
        outer = source.outer_iterator()
        while outer.has_next():
            group = outer.next()
            for item in group.items():
                try:
                    inner = item.inner_iterator()
                    while inner.has_next():
                        sub = inner.next()
                        consume(sub)
                except InnerError:
                    use_default(item)
'''
        self.verify_matrix_decompilation(source, 'Q25')

    def test_Q26_five_level_for_try_if_for_try(self):
        """Q26: for>try>if>for>try - 双try五层"""
        source = '''
def func(streams):
    for stream in streams:
        try:
            header = stream.read_header()
            if header.valid():
                records = header.records()
                for rec in records:
                    try:
                        parse_and_store(rec)
                    except ParseError:
                        store_raw(rec)
        except StreamError:
            mark_stream_broken(stream)
'''
        self.verify_matrix_decompilation(source, 'Q26')

    def test_Q27_five_level_while_if_for_if_while(self):
        """Q27: while>if>for>if>while - 条件密集型五层"""
        source = '''
def func(engine):
    while engine.running():
        state = engine.current_state()
        if state.processable():
            tasks = state.tasks()
            for task in tasks:
                if task.ready():
                    steps = task.steps()
                    s = 0
                    while s < len(steps):
                        engine.execute(steps[s])
                        s += 1
'''
        self.verify_matrix_decompilation(source, 'Q27')

    def test_Q28_five_level_with_for_if_while_try(self):
        """Q28: with>for>if>while>try - 含上下文管理器的五层"""
        source = '''
def func(lockfile, queue):
    with acquire_lock(lockfile) as lock:
        items = queue.drain()
        for item in items:
            if item.should_process():
                attempts = 0
                while attempts < MAX_RETRIES:
                    try:
                        process_under_lock(item, lock)
                        break
                    except LockConflict:
                        attempts += 1
'''
        self.verify_matrix_decompilation(source, 'Q28')

    def test_Q29_five_level_try_except_for_if_while(self):
        """Q29: try>except>for>if>while - 完整异常处理五层"""
        source = '''
def func(raw):
    try:
        parsed = parse(raw)
    except ParseError:
        parsed = empty_structure()
    else:
        entries = parsed.entries()
        for entry in entries:
            if entry.has_subentries():
                sub = entry.subentries()
                idx = 0
                while idx < len(sub):
                    process(sub[idx])
                    idx += 1
'''
        self.verify_matrix_decompilation(source, 'Q29')

    def test_Q30_five_level_if_for_try_except_else_for(self):
        """Q30: if>for>try>except>else>for - 含else分支的五层"""
        source = '''
def func(flag, data):
    if flag:
        for chunk in data.chunks():
            try:
                items = decompress(chunk)
            except DecompressError:
                items = []
            else:
                items = enhance(items)
            for item in items:
                output(item)
'''
        self.verify_matrix_decompilation(source, 'Q30')

    def test_Q31_five_level_for_while_try_if_for_while(self):
        """Q31: for>while>try>if>for>while - 六层前奏（双for+双while+try+if）"""
        source = '''
def func(groups):
    for group in groups:
        iter1 = group.iterator()
        while iter1.has_next():
            elem = iter1.next()
            try:
                if elem.complex():
                    sub = elem.decompose()
                    for part in sub:
                        piter = part.processor()
                        while piter.active():
                            piter.step()
            except DecomposeError:
                elem.use_simple_path()
'''
        self.verify_matrix_decompilation(source, 'Q31')

    def test_Q32_five_level_nested_break_continue(self):
        """Q32: 五层嵌套中的break/continue组合"""
        source = '''
def func(matrix):
    result = []
    for i in range(len(matrix)):
        if matrix[i]:
            j = 0
            while j < len(matrix[i]):
                cell = matrix[i][j]
                if cell is None:
                    j += 1
                    continue
                try:
                    for k in range(cell.count()):
                        val = cell.get(k)
                        if val == SENTINEL:
                            break
                        result.append(val)
                except CellError:
                    j += 1
                    continue
                j += 1
    return result
'''
        self.verify_matrix_decompilation(source, 'Q32')

    def test_Q33_five_level_with_try_for_if_while(self):
        """Q33: with>try>for>if>while - 上下文+异常+三层嵌套"""
        source = '''
def func(transaction, records):
    with transaction.begin() as tx:
        try:
            validated = validate_all(records)
        except ValidationError as e:
            tx.rollback()
            raise
        for rec in validated:
            if rec.applicable():
                ops = rec.operations()
                op_idx = 0
                while op_idx < len(ops):
                    tx.execute(ops[op_idx])
                    op_idx += 1
        tx.commit()
'''
        self.verify_matrix_decompilation(source, 'Q33')

    def test_Q34_five_level_if_try_for_while_except(self):
        """Q34: if>try>for>while>except - 条件门控的异常处理深层"""
        source = '''
def func(mode, pipeline):
    if mode == "batch":
        try:
            stages = pipeline.stages()
            for stage in stages:
                workers = stage.workers()
                w = 0
                while w < len(workers):
                    workers[w].process()
                    w += 1
        except PipelineError:
            pipeline.reset()
'''
        self.verify_matrix_decompilation(source, 'Q34')

    def test_Q35_five_level_for_if_try_while_except_else(self):
        """Q35: for>if>try>while>except>else - 最完整的五层结构"""
        source = '''
def func(items):
    outcomes = []
    for item in items:
        if item.processable():
            try:
                handler = item.get_handler()
                retries = 0
                while retries < MAX_RETRIES:
                    result = handler.run(item)
                    if result.success():
                        break
                    retries += 1
            except HandlerTimeout:
                outcomes.append(("timeout", item))
            else:
                outcomes.append(("ok", item.id()))
    return outcomes
'''
        self.verify_matrix_decompilation(source, 'Q35')

    # ========================================================================
    # Q36-Q45: 6-8层极限深度 (extreme depth stress testing)
    # ========================================================================

    @pytest.mark.slow
    def test_Q36_six_level_alternating(self):
        """Q36: 六层交替嵌套 - for>if>while>for>if>while"""
        source = '''
def func(a, b):
    results = []
    for i in a:
        if i.active:
            j = 0
            while j < len(b):
                if b[j].match(i):
                    for sub in i.subs():
                        k = 0
                        while k < len(sub):
                            if sub[k].valid():
                                results.append(sub[k])
                            k += 1
                j += 1
    return results
'''
        self.verify_matrix_decompilation(source, 'Q36', min_equivalence=0.78)

    @pytest.mark.slow
    def test_Q37_six_level_try_wrapped(self):
        """Q37: 六层 - try>for>if>while>for>if"""
        source = '''
def func(source):
    try:
        pages = source.pages()
        for page in pages:
            if page.loaded():
                sections = page.sections()
                s = 0
                while s < len(sections):
                    sec = sections[s]
                    for block in sec.blocks():
                        if block.has_content():
                            extract(block)
                    s += 1
    except SourceReadError:
        recover_source(source)
'''
        self.verify_matrix_decompilation(source, 'Q37', min_equivalence=0.78)

    @pytest.mark.slow
    def test_Q38_seven_level_dense(self):
        """Q38: 七层密集嵌套 - if>for>if>while>if>for>if"""
        source = '''
def func(data):
    total = 0
    if data:
        for row in data.rows():
            if row.filtered():
                cols = row.columns()
                c = 0
                while c < len(cols):
                    cell = cols[c]
                    if cell.numeric():
                        for digit in cell.digits():
                            if digit > 0:
                                total += digit
                    c += 1
    return total
'''
        self.verify_matrix_decompilation(source, 'Q38', min_equivalence=0.75)

    @pytest.mark.slow
    def test_Q39_seven_level_mixed_structures(self):
        """Q39: 七层混合结构 - with>for>try>if>while>for>if"""
        source = '''
def func(resource, data):
    with manage(resource) as mgr:
        for chunk in data.chunks():
            try:
                parsed = parse(chunk)
                if parsed.ok():
                    items = parsed.items()
                    i = 0
                    while i < len(items):
                        sub = items[i].expand()
                        for part in sub:
                            if part.ready():
                                mgr.handle(part)
                        i += 1
            except ParseError:
                mgr.skip(chunk)
'''
        self.verify_matrix_decompilation(source, 'Q39', min_equivalence=0.75)

    @pytest.mark.slow
    def test_Q40_eight_level_for_dominant(self):
        """Q40: 八层for主导 - for>if>for>if>for>if>for>if (4组for-if)"""
        source = '''
def func(dims):
    count = 0
    for i1 in range(dims[0]):
        if condition1(i1):
            for i2 in range(dims[1]):
                if condition2(i1, i2):
                    for i3 in range(dims[2]):
                        if condition3(i1, i2, i3):
                            for i4 in range(dims[3]):
                                if condition4(i1, i2, i3, i4):
                                    count += 1
    return count
'''
        self.verify_matrix_decompilation(source, 'Q40', min_equivalence=0.72)

    @pytest.mark.slow
    def test_Q41_six_level_with_exceptions(self):
        """Q41: 六层+多重异常 - try>for>if>try>while>except"""
        source = '''
def func(pipeline):
    try:
        stages = pipeline.stages()
        for stage in stages:
            if stage.enabled():
                try:
                    tasks = stage.tasks()
                    t = 0
                    while t < len(tasks):
                        run_task(tasks[t])
                        t += 1
                except StageError as se:
                    log_stage_error(stage, se)
    except PipelineFatalError:
        emergency_shutdown(pipeline)
'''
        self.verify_matrix_decompilation(source, 'Q41', min_equivalence=0.78)

    @pytest.mark.slow
    def test_Q42_deep_nested_elif_chain(self):
        """Q42: 深层嵌套中的长elif链 - for>if>elif>elif>...>for"""
        source = '''
def func(items):
    for item in items:
        if item.type == "A":
            process_a(item)
        elif item.type == "B":
            process_b(item)
        elif item.type == "C":
            sub = item.components()
            for c in sub:
                handle_c(c)
        elif item.type == "D":
            process_d(item)
        else:
            process_default(item)
'''
        self.verify_matrix_decompilation(source, 'Q42', min_equivalence=0.80)

    @pytest.mark.slow
    def test_Q43_six_level_control_flow_stress(self):
        """Q43: 六层控制流压力测试 - 含break/continue/return"""
        source = '''
def func(search_space):
    for region in search_space.regions():
        if region.searchable():
            points = region.points()
            p = 0
            while p < len(points):
                point = points[p]
                try:
                    for candidate in point.neighbors():
                        if candidate.is_target():
                            return candidate
                except NeighborError:
                    p += 1
                    continue
                p += 1
            else:
                continue
        break
    return None
'''
        self.verify_matrix_decompilation(source, 'Q43', min_equivalence=0.78)

    @pytest.mark.slow
    def test_Q44_seven_level_try_finally_deep(self):
        """Q44: 七层含finally - for>if>try>for>while>finally>if"""
        source = '''
def func(work_units):
    completed = []
    for unit in work_units:
        if unit.valid():
            try:
                steps = unit.steps()
                for step in steps:
                    retry = 0
                    while retry < MAX_RETRY:
                        try:
                            execute(step)
                            break
                        except RetryableError:
                            retry += 1
            finally:
                if unit.tracking_enabled():
                    unit.record_completion()
                    completed.append(unit.id())
    return completed
'''
        self.verify_matrix_decompilation(source, 'Q44', min_equivalence=0.75)

    @pytest.mark.slow
    def test_Q45_eight_level_while_variant(self):
        """Q45: 八层while变体 - while>if>while>if>while>if>while>if"""
        source = '''
def func(state):
    results = []
    i = 0
    while i < state.depth():
        level = state.level(i)
        if level.active():
            j = 0
            while j < level.width():
                cell = level.cell(j)
                if cell.filled():
                    k = 0
                    while k < cell.layers():
                        layer = cell.layer(k)
                        if layer.visible():
                            m = 0
                            while m < layer.pixels():
                                results.append(layer.pixel(m))
                                m += 1
                        k += 1
                j += 1
        i += 1
    return results
'''
        self.verify_matrix_decompilation(source, 'Q45', min_equivalence=0.72)

    # ========================================================================
    # Q46-Q55: 特殊场景 (special scenarios)
    # ========================================================================

    def test_Q46_deep_nesting_empty_body(self):
        """Q46: 深层嵌套空体 - for>if>while>pass

        深层嵌套中某些层级只有pass语句。"""
        source = '''
def func(x):
    for i in range(5):
        if i > x:
            while False:
                pass
'''
        self.verify_matrix_decompilation(source, 'Q46')

    def test_Q47_deep_nesting_single_statement(self):
        """Q47: 深层嵌套单语句体 - 每层仅一条语句"""
        source = '''
def func(a, b, c, d):
    if a:
        if b:
            if c:
                if d:
                    result = a + b + c + d
'''
        self.verify_matrix_decompilation(source, 'Q47')

    def test_Q48_deep_nesting_early_return(self):
        """Q48: 深层嵌套提前返回 - 多层if中的早期return"""
        source = '''
def func(config, data):
    if not config.valid():
        return INVALID_CONFIG
    if not data.ready():
        return DATA_NOT_READY
    if data.empty():
        return EMPTY_RESULT
    for item in data:
        if not item.processable():
            continue
        try:
            result = process(item)
            return result
        except ProcessError:
            return PROCESS_FAILED
    return NO_RESULTS
'''
        self.verify_matrix_decompilation(source, 'Q48')

    def test_Q49_deep_nesting_for_else_while_else(self):
        """Q49: 深层嵌套for-else和while-else"""
        source = '''
def func(data):
    all_found = True
    for group in data.groups():
        found = False
        if group.searchable():
            items = group.items()
            i = 0
            while i < len(items):
                if items[i].target():
                    found = True
                    break
                i += 1
            else:
                all_found = False
        if not found:
            all_found = False
    return all_found
'''
        self.verify_matrix_decompilation(source, 'Q49')

    def test_Q50_deep_nesting_tuple_unpack_in_loop(self):
        """Q50: 深层嵌套中的元组解包 - for>if>(a,b)>while"""
        source = '''
def func(pairs):
    results = []
    for pair in pairs:
        if isinstance(pair, tuple) and len(pair) == 2:
            key, value = pair
            i = 0
            while i < len(value):
                if value[i]:
                    results.append((key, value[i]))
                i += 1
    return results
'''
        self.verify_matrix_decompilation(source, 'Q50')

    def test_Q51_deep_nesting_walrus_operator(self):
        """Q51: 深层嵌套中的海象运算符 - if>(n:=...)>while"""
        source = '''
def func(data):
    results = []
    for item in data:
        if (matched := re.match(pattern, item)):
            group = matched.group(1)
            i = 0
            while (part := get_part(group, i)):
                results.append(part)
                i += 1
    return results
'''
        self.verify_matrix_decompilation(source, 'Q51', min_equivalence=0.80)

    def test_Q52_deep_nesting_boolean_short_circuit(self):
        """Q52: 深层嵌套中的布尔短路 - if>(a and b and c)>for"""
        source = '''
def func(entries):
    for entry in entries:
        if (entry.valid() and entry.complete() and entry.verified()):
            sub = entry.content()
            for item in sub:
                if item.ready():
                    dispatch(item)
'''
        self.verify_matrix_decompilation(source, 'Q52')

    def test_Q53_deep_nesting_assignment_expression_chain(self):
        """Q53: 深层赋值表达式链 - while>(x:=...)>if>(y:=...)"""
        source = '''
def func(iterator):
    results = []
    while (chunk := iterator.next_chunk()):
        if chunk.header:
            header = chunk.header
            if (parsed := parse_header(header)):
                for field in parsed.fields():
                    results.append(field)
    return results
'''
        self.verify_matrix_decompilation(source, 'Q53', min_equivalence=0.80)

    def test_Q54_deep_nesting_multiple_excepthandlers(self):
        """Q54: 深层嵌套+多个except处理器"""
        source = '''
def func(jobs):
    for job in jobs:
        if job.priority == CRITICAL:
            try:
                run_critical(job)
            except CriticalError:
                alert_admin(job)
            except TimeoutError:
                retry_later(job)
            except MemoryError:
                reduce_load_and_retry(job)
            else:
                mark_complete(job)
'''
        self.verify_matrix_decompilation(source, 'Q54')

    def test_Q55_deep_nesting_comprehension_inside(self):
        """Q55: 深层嵌套内的推导式 - for>if>[listcomp]>while"""
        source = '''
def func(data):
    results = []
    for group in data:
        if group.transformable():
            transformed = [process(x) for x in group.items() if x.valid()]
            i = 0
            while i < len(transformed):
                results.append(transformed[i])
                i += 1
    return results
'''
        self.verify_matrix_decompilation(source, 'Q55')


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

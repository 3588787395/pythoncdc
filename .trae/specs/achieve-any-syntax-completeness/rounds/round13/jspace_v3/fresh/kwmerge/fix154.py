# fix154.py: [v154-KWMERGE] ordered kwargs-splat channel for ASTCall
#   `f(**a, k=v)` / `f(**a, **b)` compile to BUILD_MAP 0; LOAD a; DICT_MERGE 1;
#   {k:v}; DICT_MERGE 1; CALL_FUNCTION_EX 1. The reconstructor emits the ordered
#   kwargs list [KeywordStarred(a), keyword(k=v)] (verified), but
#   ast_converter._convert_call stores splats in a SINGLE local `kw_arg`
#   (later entries overwrite earlier ones) and ASTCall models one `kw` splat —
#   every splat except the last is dropped (difflib-adjacent tarfile
#   tar_filter/data_filter `member.replace(**new_attrs, deep=False)` renders
#   `member.replace(**({'deep': False}))` = real R1, new_attrs lost). Fix:
#   ordered kwargs channel — ASTCall gains a `kw_ordered` list (ASTKeyword
#   entries = named keywords, any other ASTNode = **splat value); _convert_call
#   builds it preserving the reconstructor's order whenever a splat precedes a
#   keyword or multiple splats exist (single-splat-only forms keep the legacy
#   kwparams/var/kw path bit-for-bit); the ASTCall renderer emits the ordered
#   entries in source order.
import io

# ---------- 1. ASTCall: kw_ordered slot ----------
p1 = r'F:/Downloads/pythoncdc-main/core/ast_nodes.py'
s1 = io.open(p1, encoding='utf-8-sig').read()

a = """    __slots__ = ('_func', '_pparams', '_kwparams', '_var', '_kw', 'offset')
    
    def __init__(self, func: 'ASTNode', pparams: List['ASTNode'] = None, 
                 kwparams: List['ASTKeyword'] = None, var: 'ASTNode' = None, kw: 'ASTNode' = None):
        super().__init__(NodeType.NODE_CALL)
        self._func = func
        self._pparams = pparams if pparams is not None else []
        self._kwparams = kwparams if kwparams is not None else []
        self._var = var
        self._kw = kw"""
assert a in s1, 'astcall slots'
r = """    __slots__ = ('_func', '_pparams', '_kwparams', '_var', '_kw', '_kw_ordered', 'offset')

    def __init__(self, func: 'ASTNode', pparams: List['ASTNode'] = None,
                 kwparams: List['ASTKeyword'] = None, var: 'ASTNode' = None, kw: 'ASTNode' = None,
                 kw_ordered: List['ASTNode'] = None):
        super().__init__(NodeType.NODE_CALL)
        self._func = func
        self._pparams = pparams if pparams is not None else []
        self._kwparams = kwparams if kwparams is not None else []
        self._var = var
        self._kw = kw
        # [v154-KWMERGE] 保序 kwargs 通道：元素为 ASTKeyword（具名关键字）或
        # 其他 ASTNode（**expr 溅射值）。仅当溅射先于具名关键字或存在多个溅射
        # 时由 ast_converter._convert_call 填充（重建器 kwargs 列表的源级顺序）；
        # 单溅射形维持 kwparams/var/kw 旧路径逐位不变。
        self._kw_ordered = kw_ordered if kw_ordered is not None else []"""
s1 = s1.replace(a, r, 1)

a = """    @property
    def kwparams(self) -> List['ASTKeyword']:
        return self._kwparams"""
assert a in s1, 'astcall kwparams prop'
r = """    @property
    def kwparams(self) -> List['ASTKeyword']:
        return self._kwparams

    @property
    def kw_ordered(self) -> List['ASTNode']:
        return self._kw_ordered"""
s1 = s1.replace(a, r, 1)
io.open(p1, 'w', encoding='utf-8-sig').write(s1)
print('ASTCall extended')

# ---------- 2. ast_converter._convert_call: build ordered entries ----------
p2 = r'F:/Downloads/pythoncdc-main/core/cfg/ast_converter.py'
s2 = io.open(p2, encoding='utf-8-sig').read()

a = """        # [关键修复] 处理关键字参数，包括KeywordStarred（**kwargs）
        kwparams = []
        kwargs = expr_dict.get('kwargs', []) or expr_dict.get('keywords', [])
        if kwargs:
            for kw in kwargs:
                if isinstance(kw, dict):
                    if kw.get('type') == 'keyword':
                        kw_value = self._convert_expression(kw.get('value', {}))
                        if kw_value:
                            from core.ast_nodes import ASTKeyword
                            kwparams.append(ASTKeyword(name=kw.get('arg'), value=kw_value))
                    elif kw.get('type') == 'KeywordStarred':
                        # **kwargs 参数
                        kw_arg = self._convert_expression(kw.get('value', {}))"""
assert a in s2, 'convert_call kw head'
r = """        # [关键修复] 处理关键字参数，包括KeywordStarred（**kwargs）
        kwparams = []
        kwargs = expr_dict.get('kwargs', []) or expr_dict.get('keywords', [])
        # [v154-KWMERGE] 保序收集：存在多个 **splat 或 splat 先于具名关键字时，
        # 按重建器 kwargs 列表的源级顺序构建 kw_ordered（ASTKeyword=具名、
        # 其他 ASTNode=**splat 值）；否则维持旧 kwparams/var/kw 路径逐位不变。
        _v154_splat_idx = None
        _v154_named_idx = None
        _v154_splat_count = 0
        if kwargs:
            for _v154_i, _v154_kw in enumerate(kwargs):
                if not isinstance(_v154_kw, dict):
                    continue
                if _v154_kw.get('type') == 'KeywordStarred':
                    _v154_splat_count += 1
                    if _v154_splat_idx is None:
                        _v154_splat_idx = _v154_i
                elif _v154_kw.get('type') == 'keyword' and _v154_named_idx is None:
                    _v154_named_idx = _v154_i
        _v154_use_ordered = (
            kwargs is not None and len(kwargs) > 0
            and (_v154_splat_count > 1
                 or (_v154_splat_idx is not None and _v154_named_idx is not None
                     and _v154_splat_idx < _v154_named_idx)))
        _v154_kw_ordered = [] if _v154_use_ordered else None
        if kwargs:
            for kw in kwargs:
                if isinstance(kw, dict):
                    if kw.get('type') == 'keyword':
                        kw_value = self._convert_expression(kw.get('value', {}))
                        if kw_value:
                            from core.ast_nodes import ASTKeyword
                            if _v154_use_ordered:
                                _v154_kw_ordered.append(ASTKeyword(name=kw.get('arg'), value=kw_value))
                            else:
                                kwparams.append(ASTKeyword(name=kw.get('arg'), value=kw_value))
                    elif kw.get('type') == 'KeywordStarred':
                        # **kwargs 参数
                        kw_arg = self._convert_expression(kw.get('value', {}))
                        if _v154_use_ordered and kw_arg is not None:
                            _v154_kw_ordered.append(kw_arg)"""
s2 = s2.replace(a, r, 1)

a = """        if func:
            return ASTCall(func, pparams=args, kwparams=kwparams, var=var_arg, kw=kw_arg)
        return None"""
assert a in s2, 'convert_call tail'
r = """        if func:
            if _v154_use_ordered:
                return ASTCall(func, pparams=args, kwparams=kwparams,
                               kw_ordered=_v154_kw_ordered)
            return ASTCall(func, pparams=args, kwparams=kwparams, var=var_arg, kw=kw_arg)
        return None"""
s2 = s2.replace(a, r, 1)
io.open(p2, 'w', encoding='utf-8-sig').write(s2)
print('converter patched')

# ---------- 3. code_generator: render kw_ordered ----------
p3 = r'F:/Downloads/pythoncdc-main/core/cfg/code_generator.py'
s3 = io.open(p3, encoding='utf-8-sig').read()

a = """        # [关键修复] 处理关键字参数 (kwparams)
        kwparams = node.kwparams if hasattr(node, 'kwparams') else []
        for kw in kwparams:
            # [关键修复] ASTKeyword使用name而不是arg
            kw_name = getattr(kw, 'name', None) or getattr(kw, 'arg', None)
            kw_value = getattr(kw, 'value', None)
            if kw_name and kw_value:
                # [关键修复] 使用0作为parent_precedence，避免关键字参数值被添加括号
                kw_value_code = self._generate_expression(kw_value, 0)
                # [YF9-V3R4] 关键字实参值为 yield 时同样必须括号包裹
                # （`f(k=(yield x))`）。
                if isinstance(kw_value, ASTYield):
                    kw_value_code = f'({kw_value_code})'
                args_code.append(f'{kw_name}={kw_value_code}')

        # [关键修复] 处理 *args 参数
        var = node.var if hasattr(node, 'var') else None
        if var:
            var_code = self._generate_expression(var)
            # [YF9-V3R4] `*(yield x)` 解包实参必须括号包裹。
            if isinstance(var, ASTYield):
                var_code = f'({var_code})'
            args_code.append(f'*{var_code}')

        # [关键修复] 处理 **kwargs 参数
        kw = node.kw if hasattr(node, 'kw') else None
        if kw:
            kw_code = self._generate_expression(kw)
            # [YF9-V3R4] `**(yield x)` 解包实参必须括号包裹。
            if isinstance(kw, ASTYield):
                kw_code = f'({kw_code})'
            args_code.append(f'**{kw_code}')

        return f'{func_code}({", ".join(args_code)})'"""
assert a in s3, 'codegen call tail'
r = """        # [v154-KWMERGE] 保序 kwargs 通道：kw_ordered 非空时按源级顺序发射
        # （ASTKeyword=具名、其他 ASTNode=**splat 值），kwparams/var/kw 旧尾巴
        # 不再重复发射；空时逐位落回旧路径。
        _v154_kw_ordered = getattr(node, 'kw_ordered', None) or []
        if _v154_kw_ordered:
            for _v154_entry in _v154_kw_ordered:
                if type(_v154_entry).__name__ == 'ASTKeyword':
                    _v154_name = getattr(_v154_entry, 'name', None) or getattr(_v154_entry, 'arg', None)
                    _v154_value = getattr(_v154_entry, 'value', None)
                    if _v154_name and _v154_value:
                        _v154_value_code = self._generate_expression(_v154_value, 0)
                        if isinstance(_v154_value, ASTYield):
                            _v154_value_code = f'({_v154_value_code})'
                        args_code.append(f'{_v154_name}={_v154_value_code}')
                elif _v154_entry is not None:
                    _v154_splat_code = self._generate_expression(_v154_entry, 0)
                    if isinstance(_v154_entry, ASTYield):
                        _v154_splat_code = f'({_v154_splat_code})'
                    args_code.append(f'**{_v154_splat_code}')
            return f'{func_code}({", ".join(args_code)})'

        # [关键修复] 处理关键字参数 (kwparams)
        kwparams = node.kwparams if hasattr(node, 'kwparams') else []
        for kw in kwparams:
            # [关键修复] ASTKeyword使用name而不是arg
            kw_name = getattr(kw, 'name', None) or getattr(kw, 'arg', None)
            kw_value = getattr(kw, 'value', None)
            if kw_name and kw_value:
                # [关键修复] 使用0作为parent_precedence，避免关键字参数值被添加括号
                kw_value_code = self._generate_expression(kw_value, 0)
                # [YF9-V3R4] 关键字实参值为 yield 时同样必须括号包裹
                # （`f(k=(yield x))`）。
                if isinstance(kw_value, ASTYield):
                    kw_value_code = f'({kw_value_code})'
                args_code.append(f'{kw_name}={kw_value_code}')

        # [关键修复] 处理 *args 参数
        var = node.var if hasattr(node, 'var') else None
        if var:
            var_code = self._generate_expression(var)
            # [YF9-V3R4] `*(yield x)` 解包实参必须括号包裹。
            if isinstance(var, ASTYield):
                var_code = f'({var_code})'
            args_code.append(f'*{var_code}')

        # [关键修复] 处理 **kwargs 参数
        kw = node.kw if hasattr(node, 'kw') else None
        if kw:
            kw_code = self._generate_expression(kw)
            # [YF9-V3R4] `**(yield x)` 解包实参必须括号包裹。
            if isinstance(kw, ASTYield):
                kw_code = f'({kw_code})'
            args_code.append(f'**{kw_code}')

        return f'{func_code}({", ".join(args_code)})'"""
s3 = s3.replace(a, r, 1)
io.open(p3, 'w', encoding='utf-8-sig').write(s3)
print('codegen patched')

import py_compile
py_compile.compile(p1, doraise=True)
py_compile.compile(p2, doraise=True)
py_compile.compile(p3, doraise=True)
print('syntax OK')

"""Fix: fallback to _generate_block_statements when _generate_region returns empty for post-try blocks"""
path = r'f:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old = """                # 检查是否是嵌套区域的入口
                _ptb_region = self.region_analyzer.get_entry_region_for_block(_ptb)
                if _ptb_region and _ptb_region is not region:
                    _nrid = id(_ptb_region)
                    if (_nrid not in self._generated_regions
                            and _nrid not in self._generating_regions):
                        self._generating_regions.add(_nrid)
                        try:
                            _nr_ast = self._generate_region(_ptb_region)
                        finally:
                            self._generating_regions.discard(_nrid)
                        if _nr_ast:
                            if isinstance(_nr_ast, list):
                                _post_try_stmts_r19n2.extend(_nr_ast)
                            else:
                                _post_try_stmts_r19n2.append(_nr_ast)
                        for _b in _ptb_region.blocks:
                            self.generated_blocks.add(_b)
                        self._generated_regions.add(_nrid)
                        continue
                # 普通块：生成语句
                _pt_stmts = self._generate_block_statements(_ptb)"""

new = """                # 检查是否是嵌套区域的入口
                _ptb_region = self.region_analyzer.get_entry_region_for_block(_ptb)
                if _ptb_region and _ptb_region is not region:
                    _nrid = id(_ptb_region)
                    if (_nrid not in self._generated_regions
                            and _nrid not in self._generating_regions):
                        self._generating_regions.add(_nrid)
                        try:
                            _nr_ast = self._generate_region(_ptb_region)
                        finally:
                            self._generating_regions.discard(_nrid)
                        if _nr_ast:
                            if isinstance(_nr_ast, list):
                                _post_try_stmts_r19n2.extend(_nr_ast)
                            else:
                                _post_try_stmts_r19n2.append(_nr_ast)
                            for _b in _ptb_region.blocks:
                                self.generated_blocks.add(_b)
                            self._generated_regions.add(_nrid)
                            continue
                        # [dtc-r08 fix] 区域归约算法原则 2（每块唯一归属）：
                        # 当 _generate_region 返回空（如 BASIC Region 仅含
                        # `LOAD_CONST None; RETURN_VALUE` 的 post-try 块），
                        # 回退到 _generate_block_statements 生成语句，否则
                        # post-try 代码（如 `return None`）会丢失。
                        # 清除标记后重新生成
                        self.generated_blocks.discard(_ptb)
                        self.generated_offsets.discard(_ptb.start_offset)
                # 普通块：生成语句
                _pt_stmts = self._generate_block_statements(_ptb)"""

if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fix applied successfully!")
else:
    print("ERROR: Old text not found!")

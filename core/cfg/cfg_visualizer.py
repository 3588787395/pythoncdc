"""
CFG可视化模块

提供控制流图的可视化功能，支持文本和图形输出。
"""

import html
from typing import List, Dict, Optional, Set
from pathlib import Path

from .basic_block import BasicBlock
from .cfg_builder import ControlFlowGraph


class CFGTextVisualizer:
    """
    文本可视化器
    
    以文本形式可视化CFG。
    """
    
    @staticmethod
    def visualize(cfg: ControlFlowGraph, show_instructions: bool = True) -> str:
        """
        可视化CFG为文本
        
        Args:
            cfg: 控制流图
            show_instructions: 是否显示指令
            
        Returns:
            文本表示
        """
        lines = []
        lines.append("="*80)
        lines.append(f"Control Flow Graph: {cfg.name}")
        lines.append("="*80)
        lines.append(f"Total blocks: {len(cfg.blocks)}")
        lines.append(f"Entry block: {cfg.entry_block.id if cfg.entry_block else 'None'}")
        lines.append(f"Exit blocks: {[b.id for b in cfg.exit_blocks]}")
        lines.append("="*80)
        
        for block in cfg.get_blocks_in_order():
            lines.append("")
            lines.append(CFGTextVisualizer._visualize_block(block, show_instructions))
        
        return "\n".join(lines)
    
    @staticmethod
    def _visualize_block(block: BasicBlock, show_instructions: bool = True) -> str:
        """可视化单个基本块"""
        lines = []
        
        # 块头部
        header = f"Block {block.id} [offset {block.start_offset}-{block.end_offset}]"
        if block.is_entry:
            header += " [ENTRY]"
        if block.is_exit:
            header += " [EXIT]"
        if block.loop_header:
            header += f" [LOOP HEADER, depth={block.loop_depth}]"
        
        lines.append(header)
        lines.append("-" * len(header))
        
        # 前驱
        if block.predecessors:
            pred_ids = [str(p.id) for p in block.predecessors]
            lines.append(f"Predecessors: {', '.join(pred_ids)}")
        
        # 后继
        if block.successors:
            succ_ids = [str(s.id) for s in block.successors]
            lines.append(f"Successors: {', '.join(succ_ids)}")
        
        # 指令
        if show_instructions and block.instructions:
            lines.append("")
            lines.append("Instructions:")
            for instr in block.instructions:
                line_info = f"L{instr.starts_line:3}" if instr.starts_line else "   "
                target_marker = ">" if instr.is_jump_target else " "
                arg_str = f" {instr.arg}" if instr.arg is not None else ""
                lines.append(f"  {line_info} {target_marker} {instr.offset:3}: {instr.opname}{arg_str}")
        
        return "\n".join(lines)


class CFGDotVisualizer:
    """
    DOT格式可视化器
    
    生成Graphviz DOT格式的CFG表示。
    """
    
    @staticmethod
    def generate_dot(cfg: ControlFlowGraph, highlight_blocks: Optional[Set[int]] = None) -> str:
        """
        生成DOT格式
        
        Args:
            cfg: 控制流图
            highlight_blocks: 要高亮显示的块ID集合
            
        Returns:
            DOT格式字符串
        """
        if highlight_blocks is None:
            highlight_blocks = set()
        
        lines = [f'digraph "{html.escape(cfg.name)}" {{']
        lines.append('    rankdir=TB;')
        lines.append('    node [shape=box, fontname="Courier New"];')
        lines.append('    edge [fontname="Courier New"];')
        lines.append('')
        
        # 定义节点
        for block in cfg.get_blocks_in_order():
            node_id = f"block{block.id}"
            
            # 构建标签
            label_parts = [f"Block {block.id}"]
            
            if block.is_entry:
                label_parts.append("[ENTRY]")
            if block.is_exit:
                label_parts.append("[EXIT]")
            if block.loop_header:
                label_parts.append(f"[LOOP depth={block.loop_depth}]")
            
            # 添加指令摘要
            if block.instructions:
                instr_summary = CFGDotVisualizer._get_instruction_summary(block)
                if instr_summary:
                    label_parts.append(f"\\n{instr_summary}")
            
            label = "\\n".join(label_parts)
            
            # 确定颜色
            if block.id in highlight_blocks:
                color = "fillcolor=lightblue, style=filled"
            elif block.is_entry:
                color = "fillcolor=lightgreen, style=filled"
            elif block.is_exit:
                color = "fillcolor=lightyellow, style=filled"
            elif block.loop_header:
                color = "fillcolor=lightcoral, style=filled"
            else:
                color = ""
            
            if color:
                lines.append(f'    {node_id} [label="{label}", {color}];')
            else:
                lines.append(f'    {node_id} [label="{label}"];')
        
        lines.append('')
        
        # 定义边
        for block in cfg.get_blocks_in_order():
            node_id = f"block{block.id}"
            
            for succ in block.successors:
                succ_id = f"block{succ.id}"
                
                # 确定边的样式
                if succ == block:  # 自环
                    style = "color=red, style=bold"
                elif succ.dominates(block):  # 回边
                    style = "color=blue, constraint=false"
                else:
                    style = ""
                
                if style:
                    lines.append(f'    {node_id} -> {succ_id} [{style}];')
                else:
                    lines.append(f'    {node_id} -> {succ_id};')
        
        lines.append('}')
        
        return "\n".join(lines)
    
    @staticmethod
    def _get_instruction_summary(block: BasicBlock, max_instr: int = 3) -> str:
        """获取指令摘要"""
        instrs = []
        for i, instr in enumerate(block.instructions[:max_instr]):
            arg_str = f" {instr.arg}" if instr.arg is not None else ""
            instrs.append(f"{instr.opname}{arg_str}")
        
        if len(block.instructions) > max_instr:
            instrs.append("...")
        
        return "\\n".join(instrs)
    
    @staticmethod
    def save_dot(cfg: ControlFlowGraph, filename: str, highlight_blocks: Optional[Set[int]] = None) -> None:
        """
        保存DOT文件
        
        Args:
            cfg: 控制流图
            filename: 输出文件名
            highlight_blocks: 要高亮显示的块ID集合
        """
        dot_content = CFGDotVisualizer.generate_dot(cfg, highlight_blocks)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(dot_content)
    
    @staticmethod
    def render_to_image(cfg: ControlFlowGraph, output_file: str, 
                       format: str = 'png', highlight_blocks: Optional[Set[int]] = None) -> bool:
        """
        渲染CFG为图像
        
        需要安装Graphviz。
        
        Args:
            cfg: 控制流图
            output_file: 输出图像文件
            format: 图像格式（png, svg, pdf等）
            highlight_blocks: 要高亮显示的块ID集合
            
        Returns:
            是否成功
        """
        try:
            import subprocess
            import tempfile
            import os
            
            # 生成DOT内容
            dot_content = CFGDotVisualizer.generate_dot(cfg, highlight_blocks)
            
            # 创建临时DOT文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
                f.write(dot_content)
                dot_file = f.name
            
            try:
                # 调用dot命令
                result = subprocess.run(
                    ['dot', f'-T{format}', dot_file, '-o', output_file],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return True
            finally:
                os.unlink(dot_file)
                
        except FileNotFoundError:
            print("错误: 未找到Graphviz。请安装Graphviz并添加到PATH。")
            return False
        except subprocess.CalledProcessError as e:
            print(f"错误: Graphviz渲染失败: {e.stderr}")
            return False
        except Exception as e:
            print(f"错误: {e}")
            return False


class CFGHTMLVisualizer:
    """
    HTML可视化器
    
    生成交互式HTML可视化。
    """
    
    @staticmethod
    def generate_html(cfg: ControlFlowGraph, title: Optional[str] = None) -> str:
        """
        生成HTML可视化
        
        Args:
            cfg: 控制流图
            title: 页面标题
            
        Returns:
            HTML字符串
        """
        if title is None:
            title = f"CFG: {cfg.name}"
        
        # 生成DOT内容（用于嵌入）
        dot_content = CFGDotVisualizer.generate_dot(cfg)
        
        # 预处理DOT内容，转义反引号
        dot_escaped = dot_content.replace('`', '\\`')
        
        html_template = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{html.escape(title)}</title>
    <script src="https://unpkg.com/viz.js@2.1.2-pre.1/viz.js"></script>
    <script src="https://unpkg.com/viz.js@2.1.2-pre.1/full.render.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
        }}
        .info {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .info-item {{
            margin: 5px 0;
        }}
        #graph {{
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: auto;
        }}
        svg {{
            max-width: 100%;
            height: auto;
        }}
    </style>
</head>
<body>
    <h1>{html.escape(title)}</h1>
    
    <div class="info">
        <div class="info-item"><strong>总块数:</strong> {len(cfg.blocks)}</div>
        <div class="info-item"><strong>入口块:</strong> {cfg.entry_block.id if cfg.entry_block else 'None'}</div>
        <div class="info-item"><strong>出口块:</strong> {[b.id for b in cfg.exit_blocks]}</div>
    </div>
    
    <div id="graph"></div>
    
    <script>
        const dotSrc = `{dot_escaped}`;
        
        const viz = new Viz();
        viz.renderSVGElement(dotSrc)
            .then(element => {{
                document.getElementById('graph').appendChild(element);
            }})
            .catch(error => {{
                console.error(error);
                document.getElementById('graph').innerHTML = '<p style="color: red;">渲染失败: ' + error.message + '</p>';
            }});
    </script>
</body>
</html>'''
        
        return html_template
    
    @staticmethod
    def save_html(cfg: ControlFlowGraph, filename: str, title: Optional[str] = None) -> None:
        """
        保存HTML文件
        
        Args:
            cfg: 控制流图
            filename: 输出文件名
            title: 页面标题
        """
        html_content = CFGHTMLVisualizer.generate_html(cfg, title)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)


def visualize_cfg(cfg: ControlFlowGraph, format: str = 'text', **kwargs) -> Optional[str]:
    """
    便捷函数：可视化CFG
    
    Args:
        cfg: 控制流图
        format: 输出格式（text, dot, html）
        **kwargs: 额外参数
        
    Returns:
        可视化结果（文本格式）或None
    """
    if format == 'text':
        return CFGTextVisualizer.visualize(cfg, **kwargs)
    elif format == 'dot':
        return CFGDotVisualizer.generate_dot(cfg, **kwargs)
    elif format == 'html':
        return CFGHTMLVisualizer.generate_html(cfg, **kwargs)
    else:
        raise ValueError(f"不支持的格式: {format}")


# 便捷函数
def print_cfg(cfg: ControlFlowGraph, show_instructions: bool = True) -> None:
    """打印CFG到控制台"""
    print(CFGTextVisualizer.visualize(cfg, show_instructions))


def save_cfg_dot(cfg: ControlFlowGraph, filename: str) -> None:
    """保存CFG为DOT文件"""
    CFGDotVisualizer.save_dot(cfg, filename)


def save_cfg_html(cfg: ControlFlowGraph, filename: str, title: Optional[str] = None) -> None:
    """保存CFG为HTML文件"""
    CFGHTMLVisualizer.save_html(cfg, filename, title)

"""repro_11: close mirror of graph.pyc create_full_graph.

    Outer try (BaseException) wraps a for-loop building edges/nodes,
    inner try/except KeyError updates a relation dict inside the loop,
    post-loop code adds nodes/edges to a graph, returns dict.
"""
def f(node_list):
    return_dict = {'error_no': 0, 'error_info': ''}
    _nodes = []
    _edges = []
    try:
        for _info in node_list:
            if len(_info) != 0:
                _edges.append(_info)
            else:
                _nodes.append(_info)
            relation_key = str(_info)
            try:
                relation_value = _nodes[relation_key]
                relation_value.append(_info)
            except KeyError:
                _nodes = [_info]
        _edges.extend(_nodes)
        return return_dict
    except BaseException:
        return_dict['error_no'] = -1
        return_dict['error_info'] = 'err'
        return return_dict

from _ast import *

def walk(node):
    """
    Recursively yield all child nodes of *node*, in no specified order.  This is
    useful if you only want to modify nodes in place and don't care about the
    context.
    """
    from collections import deque
    todo = deque([node])
    while todo:
        node = todo.popleft()
        if isinstance(node, (Name, Call, arguments)):
            continue
#        print node, getattr(node, 'lineno', None)
        if not isinstance(node, (Call, BinOp, Dict, Tuple, List, ListComp, GeneratorExp)):
            todo.extend(iter_child_nodes(node))
        yield node

def iter_child_nodes(node):
    """
    Yield all direct child nodes of *node*, that is, all fields that are nodes
    and all items of fields that are lists of nodes.
    """
    for name, field in iter_fields(node):
        if isinstance(field, AST):
            yield field
        elif isinstance(field, list):
            for item in field:
                if isinstance(item, AST):
                    yield item

def iter_fields(node):
    """
    Yield a tuple of ``(fieldname, value)`` for each field in ``node._fields``
    that is present on *node*.
    """
    if node._fields is not None:
        for field in node._fields:
            try:
                yield field, getattr(node, field)
            except AttributeError:
                pass

def get_line_nums(source):
    cur_ast = compile(source, '<unknown>', 'exec', PyCF_ONLY_AST)
    linestarts = set()
    for node in walk(cur_ast):
        if hasattr(node, 'lineno'):
            linestarts.add(node.lineno)
#            if node.lineno == 92:
#                print '--', node, getattr(node, 'lineno', None)
#        print type(node)
    return sorted(linestarts)


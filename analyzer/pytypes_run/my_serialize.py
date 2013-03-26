#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-
import sys
import os
import binascii

all_types = ['code', 'iterator', 'generator_object', 'int', 'float', 'module', 'unicode', '::object', 'undef', 'generator', 'unknown', 'complex', 'bool', 'dict', 'metaclass', 'function', 'tuple', 'builtin_smth_callable', 'slice', '::inner_symtable', 'builtin_function_or_method', 'classmethod', 'type', 'list', 'str', 'NoneType']

real_t = ['code', 'iterator', 'generator_object', 'int', 'float', 'module', 'unicode', 'generator', 'unknown', 'complex', 'bool', 'dict', 'metaclass', 'function', 'tuple', 'builtin_smth_callable', 'slice', 'builtin_function_or_method', 'classmethod', 'type', 'list', 'str', 'NoneType']

simple_t = ['iterator', 'str', 'unicode', 'code', 'int', 'float', 'slice', 'unknown', 'complex', 'bool', 'type', 'NoneType']
iterable_t = ['dict', 'tuple', 'list']
callable_t = ['generator_object', 'module', 'generator', 'metaclass', 'function', 'builtin_smth_callable', 'builtin_function_or_method', 'classmethod']
#print 'real:', len(real_t)
#print 'sum:', len(simple_t) + len(iterable_t) + len(callable_t)


def fcode_to_uniq(fcode):
    return '%s:%s' % (fcode.co_filename, fcode.co_name)

def mcode_to_uniq(mcode):
    return '%s' % mcode.co_filename

def pcode_to_uniq(pcode):
    fn = pcode.co_filename
    if fn.endswith('__init__.py'):
        return os.path.dirname(fn)
    else:
        return fn

def module_to_uniq(m):
    fn = None
    if hasattr(m, '__file__'):
        fn = m.__file__
    else:
#        print "GOTCHA: %r" % m.__name__,  dir(m)
        fn = m.__name__
    if fn:
        if fn.endswith('.pyc'):
            fn = fn[:-1]
        fn = os.path.abspath(fn)
    return fn

def value_to_str(vname, v):
    def _get_type(v):
        return type(v).__name__
        if hasattr(v, '__class__'):
            return v.__class__.__name__
        else:
#            print 'got unknown: %r' % v
#            print '\t%s: %r' % (type(v), dir(v))
            return 'unknown'

    vtype = _get_type(v)
    vtd = {}
    if vtype in simple_t:
        vtd[vtype] = None
    elif vtype in iterable_t:
        items_types = set(map(_get_type, v))
        vtd[vtype] = {'len': len(v), 'items': items_types}
        if vtype == 'dict':
            val_types = set(map(_get_type, v.values()))
            vtd[vtype]['values'] = val_types
    elif vtype in callable_t:
        vdata = None
#        if vtype in ('function', 'instancemethod', 'classmethod'):
        if vtype in ('function', ):
            vdata = fcode_to_uniq(v.func_code)
        elif vtype == 'module':
            vdata = module_to_uniq(v)

        vtd[vtype] = vdata
    else:
#        attr_types = set([(x, _get_type(getattr(v, x))) for x in dir(v)])
        attr_types = set()
        for x in dir(v):
            try:
                attr_types.add((x, _get_type(getattr(v, x))))
            except AttributeError, e:
                pass
        vtd['::other'] = {vtype: attr_types}
    return '%s:%r' % (vname, vtd)


def _one_to_tuple(vtype, vinfo):
    # [vtype, len, attrs]
    res = [vtype, None, None]
    if vtype in simple_t:
        pass
    elif vtype in iterable_t:
        res[1] = vinfo['len']
        if vtype == 'dict':
            res[2] = (frozenset(vinfo['items']), frozenset(vinfo['values']))
        else:
            res[2] = frozenset(vinfo['items'])
    elif vtype in callable_t:
        if vtype in ('function', 'module'):
            res[2] = vinfo
    else:
        vtype = vinfo.keys()[0]
        vattrs = vinfo[vtype]
#        print vtype, vattrs
        res[0] = vtype
        res[2] = frozenset(vattrs)
    return tuple(res)

def serialized_to_hashable(s):
    vtd = eval(s)
    assert len(vtd) == 1
    vtype = vtd.keys()[0]
    vinfo = vtd[vtype]
    return _one_to_tuple(vtype, vinfo)

def dict_to_set(vtd):
    res = set()
#    print vtd
    for vtype, vinfo in vtd.items():
        res.add(_one_to_tuple(vtype, vinfo))
    return res


# -*- coding: utf-8 -*-

import sys
import itertools
from random import randint
from copy import copy, deepcopy
from itertools import *
from dis import opname


#NOTICE: 'COMPARE_OP' placed here and at VarTypes too, thus
#it will be redirected to VarTypes and processed by one
VAR_INSTS = frozenset(['BINARY_ADD', 'BINARY_AND', 'BINARY_DIVIDE', 
                       'BINARY_FLOOR_DIVIDE', 'BINARY_LSHIFT', 
                       'BINARY_MODULO', 'BINARY_MULTIPLY', 'BINARY_OR', 
                       'BINARY_POWER', 'BINARY_RSHIFT', 'BINARY_SUBSCR',
                       'BINARY_SUBTRACT', 'BINARY_TRUE_DIVIDE', 
                       'BINARY_XOR', 'BUILD_SLICE', 'BUILD_TUPLE', 
                       'COMPARE_OP', 'DELETE_ATTR', 'DELETE_SLICE+0', 
                       'DELETE_SLICE+1', 'DELETE_SLICE+2', 'FOR_ITER', 
                       'DELETE_SLICE+3', 'DELETE_SUBSCR', 'EXEC_STMT', 
                       'GET_ITER', 'INPLACE_ADD', 'INPLACE_AND', 
                       'INPLACE_DIVIDE', 'INPLACE_FLOOR_DIVIDE', 
                       'INPLACE_LSHIFT', 'INPLACE_MODULO', 
                       'INPLACE_MULTIPLY', 'INPLACE_OR', 'INPLACE_POWER',
                       'INPLACE_RSHIFT', 'INPLACE_SUBTRACT', 
                       'INPLACE_TRUE_DIVIDE', 'INPLACE_XOR', 
                       'LIST_APPEND', 'SLICE+0', 'SLICE+1',
                       'SLICE+2', 'SLICE+3', 'STORE_SLICE+0', 
                       'STORE_SLICE+1', 'STORE_SLICE+2', 'STORE_SLICE+3',
                       'STORE_SUBSCR', 'UNARY_CONVERT', 'UNARY_INVERT', 
                       'STORE_MAP',
                       'UNARY_NEGATIVE', 'UNARY_NOT', 'UNARY_POSITIVE', 
                       'UNPACK_SEQUENCE', 'LOAD_ATTR', 'STORE_ATTR', 
                       'DELETE_ATTR', ])


INPLACE_INSTS = frozenset(['STORE_MAP'])


BINARY_INSTS = frozenset(['BINARY_POWER', 'BINARY_MULTIPLY',
                'BINARY_DIVIDE', 'BINARY_MODULO', 'BINARY_ADD',
                'BINARY_SUBTRACT', 'BINARY_SUBSCR', 'BINARY_FLOOR_DIVIDE',
                'BINARY_TRUE_DIVIDE', 'BINARY_LSHIFT', 'BINARY_RSHIFT',
                'BINARY_AND', 'BINARY_XOR', 'BINARY_OR', 'COMPARE_OP',
                'INPLACE_FLOOR_DIVIDE', 'INPLACE_TRUE_DIVIDE',
                'INPLACE_ADD', 'INPLACE_SUBTRACT', 'INPLACE_MULTIPLY',
                'INPLACE_DIVIDE', 'INPLACE_MODULO', 'INPLACE_POWER',
                'INPLACE_LSHIFT', 'INPLACE_RSHIFT', 'INPLACE_AND',
                'INPLACE_XOR', 'INPLACE_OR'])

UNARY_INSTS = frozenset(['UNARY_POSITIVE', 'UNARY_NEGATIVE',
                         'UNARY_NOT', 'UNARY_CONVERT', 'UNARY_INVERT'])
    

# instructions that need VarTypes as theirs args - containers, objects with attrs
INSTS_GET_VARTYPES = frozenset(['SLICE+0', 'SLICE+1', 'SLICE+2', 
                                'SLICE+3', 'STORE_SLICE+0', 
                                'STORE_SLICE+1', 'STORE_SLICE+2',
                                'STORE_SLICE+3', 'DELETE_SLICE+0',
                                'DELETE_SLICE+1', 'DELETE_SLICE+2',
                                'DELETE_SLICE+3', 'STORE_SUBSCR', 
                                'DELETE_SUBSCR', 'LOAD_ATTR', 
                                'STORE_ATTR', 'DELETE_ATTR',
                                'LIST_APPEND', 'BINARY_SUBSCR',
                                'STORE_MAP',
                               ])

INSTS_NO_PUSH =  frozenset(['STORE_SLICE+0', 
                             'STORE_SLICE+1', 'STORE_SLICE+2',
                             'STORE_SLICE+3', 'DELETE_SLICE+0',
                             'DELETE_SLICE+1', 'DELETE_SLICE+2',
                             'DELETE_SLICE+3', 'STORE_SUBSCR', 
                             'DELETE_SUBSCR', 
                             'STORE_ATTR', 'DELETE_ATTR', 
                             'STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 
                             'DELETE_NAME', 'DELETE_FAST', 'DELETE_GLOBAL', 
                             'LIST_APPEND'
                            ])
                      

#TOS3, TOS2, TOS1, TOS

REORDER_SEQ = {'SLICE+1': (0,1),
               'SLICE+2': (0,1),
               'SLICE+3': (0,1,2),
               'STORE_SLICE+0': (1,0),
               'STORE_SLICE+1': (1,2,0),
               'STORE_SLICE+2': (1,2,0),
               'STORE_SLICE+3': (1,2,3,0),   
               'STORE_MAP': (0,2,1),   
               'STORE_SUBSCR': (1,2,0),   
               'DELETE_SLICE+1': (0,1),
               'DELETE_SLICE+2': (0,1),
               'DELETE_SLICE+3': (0,1,2),   
               'DELETE_SUBSCR': (0,1),   
               'LIST_APPEND': (0,1),
              }
for inst in BINARY_INSTS:
    REORDER_SEQ[inst] = (0, 1)

POP_INSTS = {1: frozenset(['PRINT_EXPR', 'IMPORT_STAR', 'IMPORT_FROM', 'GET_ITER',
                           'SLICE+0', 'DELETE_SLICE+0', 'PRINT_ITEM',
                           'PRINT_NEWLINE_TO',
                           'DELETE_ATTR', 'LOAD_ATTR', 'STORE_FAST',
                           'STORE_DEREF', 'STORE_GLOBAL', 'STORE_NAME',
                           'UNPACK_SEQUENCE',
                          ] + list(UNARY_INSTS)),
             2: frozenset(['SLICE+1', 'SLICE+2', 'STORE_SLICE+0',
                           'DELETE_SLICE+1', 'DELETE_SLICE+2',
                           'DELETE_SUBSCR', 'PRINT_ITEM_TO',
                           'LIST_APPEND', 'IMPORT_NAME',
                           'STORE_ATTR', 'COMPARE_OP',
                          ] + list(BINARY_INSTS)),
             3: frozenset(['SLICE+3', 'STORE_SLICE+1', 'STORE_SLICE+2',
                           'DELETE_SLICE+3', 'STORE_SUBSCR', 'EXEC_STMT',
                           'BUILD_CLASS', 'STORE_MAP',
                          ]),
             4: frozenset(['STORE_SLICE+3', ]),
             'depends': frozenset(['BUILD_TUPLE',
                                   'RAISE_VARARGS', 'MAKE_CLOSURE',
                                   'MAKE_FUNCTION', 'BUILD_SLICE', 
                                   'BUILD_LIST']),
            }


def get_pop_count(inst):
    inst_name = opname[inst[1]]
    for i in POP_INSTS:
        if inst_name in POP_INSTS[i]:
            count = i
            break
    else:
        return 0
    if count == 'depends':
        if inst_name in ('BUILD_TUPLE', 'BUILD_LIST',
                         'BUILD_SLICE', 'RAISE_VARARGS'):
            count = inst[2]
        elif inst_name == 'MAKE_FUNCTION':
            count = inst[2] + 1
        elif inst_name == 'MAKE_CLOSURE':
            count = inst[2] + 2
        else:
            raise NotImplementedError("Unknown instruction at get_pop_count: %r" % inst_name)
    return count

def reorder(inst, vars_dlt, do_nothing = False):
    print "REORDER_FUNC", inst, vars_dlt
    if opname[inst[1]] in REORDER_SEQ and not do_nothing:
        assert len(vars_dlt) == len(REORDER_SEQ[opname[inst[1]]])
#        print "GOTCHA", [vars_dlt[i] for i in REORDER_SEQ[opname[inst[1]]]]
        return [vars_dlt[i] for i in REORDER_SEQ[opname[inst[1]]]]
    elif do_nothing and opname[inst[1]] in BINARY_INSTS:
        return [vars_dlt[i] for i in (1,0)]
    else:
        return tuple(reversed(vars_dlt))

def get_const_typename(const):
    return get_typename(type(const).__name__)

def get_typename(typename):
    if typename.find('iterator') != -1:
        typename = 'iterator'
    if typename not in VarTypes.types_classes:
        typename = 'unknown'
    return typename

def bin_prepare(inst, op1, op2):
    if op1 is None and op2 is not None:
        op1, op2 = op2, None
        return 
    if opname[inst[1]] in ('BINARY_MULTIPLY', 'INPLACE_MULTIPLY'):
        if isinstance(op2, TypeSuperContainer) and \
           isinstance(op1, TypeSimple):
            op1, op2 = op2, op1
            return

def check_parameters(vars, var_types):
    return all(map(lambda v, vt: isinstance(v, vt) or v is None, 
                   vars, var_types))



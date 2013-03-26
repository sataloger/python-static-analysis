# -*- coding: utf-8 -*-

import sys
import itertools
from random import randint
from copy import copy, deepcopy
from itertools import *
from pytypes_run.var_operations import *
from pytypes_run.base_classes import *
from pytypes_run.type_unknown import ParentType

class TypeTuple(ParentType):
    implemented_types = ('tuple',)

    def __init__(self, maxlen, maxlen_name):
        ParentType.__init__(self)
        self.values = set()
        self.length = 0
        self.maxlen = maxlen
        self.maxlen_name = maxlen_name
        self.len_fixed = False
        # FIXME : wtf is stored_types??
        self.stored_types = set(self.implemented_types)

    def _repr_inner(self):
        return ('%s_%s([' % (self.clsname, str(self.length))) + \
               '], ['.join([', '.join(map(repr,[value for value in curset]))
                           for curset in self.values]) + '])'

    def _pretty_inner(self):
        if self.length:
            return ('%s_%s([' % (self.implemented_types[0], str(self.length))) + \
                   '], ['.join([', '.join(map(repr,[value for value in curset]))
                               for curset in self.values]) + '])'
        else:
            return '%s_0' % self.implemented_types[0]

    def _list_names(self):
        res = set()
        for curset in self.values:
            res.add((self.implemented_types[0], self.length, tuple(curset)))
        return res

    def __deepcopy__(self, memo):
        res = self.__class__(self.maxlen, self.maxlen_name)
        res.fix_length(self.length)
        res.values = deepcopy(self.values)
        return res

    def clear(self):
        self.values.clear()

    def fix_length(self, length):
        if self.len_fixed:
            raise Exception('In %s: length had already been fixed' % self.clsname)
        if length != self.maxlen_name and length > self.maxlen:
            self.length = self.maxlen_name
        else:
            self.length = length
        self.len_fixed = True

    def create_from_const(self, value):
        if value is None:
            self.stored_types = set(self.implemented_types)
            self.values = set([frozenset(['unknown'])])
            self.length = self.maxlen_name
        else:
            self.stored_types = set([type(value).__name__])
            self.values = set([frozenset([get_const_typename(item)
                                          for item in value])])
            self.__length = len(value)
        self.len_fixed = True
        self.check_current_type()

    def create_from(self, other):
        self.stored_types = deepcopy(other.stored_types)
        self.values = deepcopy(other.values)
        self.length = other.length
        self.len_fixed = True

    def create_from_iterable(self, other):
        self.values = deepcopy(other.values)
        self.length = self.maxlen_name
        self.len_fixed = True

    def add_const(self, const):
        if const is None:
            self.values.add(frozenset(['unknown']))
            return
        if len(const) != self.length and \
           not (self.length == self.maxlen_name and \
                len(const) > self.maxlen):
            raise Exception("In %s.add_const: lengths differ(%r:%r)" % \
                            (self.clsname, self.length, len(const)))

        self.values.add(frozenset([get_const_typename(item)
                                   for item in const]))


    def add_type(self, other):
        self.stored_types.update(other.stored_types)
        self.values.update(deepcopy(other.values))
        if self.length != other.length:
            self.length = self.maxlen_name


    def _lge_inner(self, other):
        if self.length != other.length:
            print self
            print other
            raise Exception("Couldn't compare tuples with unequal length(%r:%r)" % \
                              (self.length, other.length))

        less = self.values < other.values
        greater = self.values > other.values
        equal = self.values == other.values
        return (less, greater, equal)


    def __nonzero__(self):
        return len(self.values)

    #def mul(self, vars):
        #other = vars[0]
        #res = self.__class__(self.maxlen, self.maxlen_name)
        #res.values = deepcopy(self.values)
        #res.len_fixed = True
        #res.length = self.maxlen_name
        #return res

    def iadd(self, other):
        if other is None:
            self.values.add(frozenset(['unknown']))
            self.len_fixed = True
            self.length = self.maxlen_name
        else:
            self.len_fixed = True
            new_values = set()
            if self.values:
                for sv in self.values:
                    new_values.update([sv | ov for ov in other.values])
            else:
                new_values = deepcopy(other.values)
            if self.length == self.maxlen_name or \
               other.length == other.maxlen_name or \
               self.length + other.length > self.maxlen:
                self.length = self.maxlen_name
            else:
                self.length = self.length + other.length
            self.values = new_values
        return self

    def add(self, vars):
        res = deepcopy(self)
        return res.iadd(vars[0])

    #def unpack_sequence(self, inst):
        #init_types = {}
        #for name in self.values:
            #if name in TypeSimple.implemented_types:
                #init_types[name] = None
            #else:
                #our_tpname = get_typename(name)
                #if our_tpname in VarTypes.containers:
                    #cur_len = name.split('_')[1]
                    #init_types[our_tpname] = {cur_len: None}
                #else:
                    #init_types[our_tpname] = None
        #return [VarTypes(init_types=init_types) for i in range(inst[2])]


    def build(self, vars):
        if len(vars) > self.maxlen:
            self.length = self.maxlen_name
        else:
            self.length = len(vars)
        self.len_fixed = True
        cur_values = set()
        for var in vars:
            for typename in var["types"].types:
                if typename == 'TypeSimple':
                    cur_values.update(var["types"].types[typename].stored_types)
                else:
                    cur_values.update(var["types"].types[typename].implemented_types)
        self.values = set([frozenset(cur_values)])


class TypeSuperContainer(ParentType):
    insts_handler = deepcopy(ParentType.insts_handler)
    implemented_insts = insts_handler.stored_insts

    def __init__(self, maxlen, maxlen_name, cont_class=None):
        ParentType.__init__(self)
        self.maxlen = maxlen
        self.maxlen_name = maxlen_name
        if cont_class is not None:
            self.cont_class = cont_class
        self.values = {}
        self.check_length('TEST13')

    def _repr_inner(self):
        res_lst = []
        for tpl in self.values.values():
            res_lst.append(repr(tpl))
        return ('%s([' % self.clsname)+ '], ['.join(res_lst) + '])'

    def _pretty_inner(self):
        res_lst = []
        for tpl in self.values.values():
            res_lst.append(repr(tpl))
        return ', '.join(res_lst)

    def _list_names(self):
        res = set()
        for tpl in self.values.values():
            res.update(tpl._list_names())
        return res

    def __deepcopy__(self, memo):
        res = self.__class__(self.maxlen, self.maxlen_name,
                             self.cont_class)
        res.values = deepcopy(self.values)
        res.check_length('TEST6')
        return res

    def clear(self):
        self.values.clear()

    def check_length(self, msg=None):
        for l in self.values:
            if l != self.values[l].length:
                print l, self.values[l].length, self
                raise Exception('Length name and real value mismatch')
    
    def create(self, value):
        tmp_cont = self.cont_class(self.maxlen, self.maxlen_name)
        tmp_cont.create(value)
        self.values = {tmp_cont.length:tmp_cont}
        self.check_length('TEST1')

    def add_const(self, const):
        if const is None:
            cur_len = self.maxlen + 1
        else:
            cur_len = len(const)
        cur_name = self.try_add_cont(cur_len)
        self.values[cur_name] |= const
        self.check_length('TEST3')

    def try_add_cont(self, cont_len):
        if cont_len > self.maxlen:
            cont_name = self.maxlen_name
        else:
            cont_name = cont_len
        if cont_name not in self.values:
            self.values[cont_name] = self.cont_class(self.maxlen,
                                                    self.maxlen_name)
            self.values[cont_name].fix_length(cont_name)

        self.check_length('TEST4')
        return cont_name

    def add_type(self, other):
        other.check_length('TEST11')
        intersect = set(self.values) & set(other.values)
        diff = set(other.values) - set(self.values)
        for tpl_name in intersect:
            self.values[tpl_name] |= other.values[tpl_name]
            self.check_length('TEST5')
        for tpl_name in diff:
            self.values[tpl_name] = deepcopy(other.values[tpl_name])
            self.check_length('TEST2')
        self.check_length('TEST7')

    def _lge_inner(self, other):
        all_keys = set(self.values.keys()) | set(other.values.keys())
        lge_list = []
        for curkey in all_keys:
            if curkey in self.values:
                if curkey not in other.values:
                    lge_list.append((0,1,0))
                else:
                    lge_list.append(self.values[curkey].lge(other.values[curkey]))
            else:
                if curkey in other.values:
                    lge_list.append((1,0,0))
                else:
                    lge_list.append((0,0,1))
                    raise Exception('Impossible situation')
        if lge_list:
            if len(lge_list) > 1:
                return map(all, map(None, *lge_list))
            else:
                return lge_list[0]
        else:
            return (0,0,1)

    def __nonzero__(self):
        return len(self.values)

    def mul(self, vars):
        res = {"types":self.__class__(self.maxlen, self.maxlen_name,
                            self.cont_class)}

        cur_name = res["types"].try_add_cont(self.values.__len__()) #(self.maxlen)
        for cont in self.values.values():
            res["types"].values[cur_name] |= cont
        res["types"].check_length('TEST8')
        return res

    def add(self, vars):
        res = {"types":self.__class__(self.maxlen, self.maxlen_name,
                             self.cont_class)}
        other = vars[0]["types"]
#        print "Adding at %r: %r" % (self, vars)
        for st in self.values.values():
            for ot in other.values.values():
                if st.length == st.maxlen_name or \
                   ot.length == ot.maxlen_name or \
                   st.length + ot.length > res["types"].maxlen:
                    cur_len = self.maxlen + 1
                else:
                    cur_len = st.length + ot.length
                cur_name = res["types"].try_add_cont(cur_len)
                res["types"].values[cur_name] |= st.add((ot,))
        res["types"].check_length('TEST9')
        return res

    def unpack_sequence(self, inst):
        init_types = {}
        for tpl in self.values.values():
            for names in tpl.values:
                for name in names:
                    init_types[name] = None
        from pytypes_run.var_types import VarTypes
        return {"types":[VarTypes(init_types=init_types) for i in range(inst[2])]}

    def get_united_element(self):
        init_types = {}
        for tpl in self.values.values():
            for names in tpl.values:
                for name in names:
                    init_types[name] = None
        return {"types":VarTypes(init_types=init_types)}

    def get_slice(self, inst, vars):
        if opname[inst[1]] == 'SLICE+0':
            return deepcopy(self)
        res = {"types":self.__class__(self.maxlen, self.maxlen_name,
                             self.cont_class)}
        res_values = self.cont_class(self.maxlen, self.maxlen_name)
        for sl in self.values.values():
            res_values.iadd(sl)
        res_values.length = self.maxlen_name
        res["types"].values = {self.maxlen_name: res_values}
        res["types"].check_length('TEST22')
        return res
        
    def build(self, vars):
        tpl = self.cont_class(self.maxlen, self.maxlen_name)
        tpl.build(vars)
        self.values = {tpl.length:tpl}
        self.check_length('TEST10')

    insts_handler.add_set(InstSet(['BINARY_ADD', 'INPLACE_ADD'], add))
    insts_handler.add_set(InstSet(['BINARY_MULTIPLY', 'INPLACE_MULTIPLY'], mul))
    insts_handler.add_set(InstSet(['UNPACK_SEQUENCE'], unpack_sequence))
    insts_handler.add_set(InstSet(['SLICE+0', 'SLICE+1', 'SLICE+2', 
                                   'SLICE+3'], get_slice))

    insts_handler.add_set(InstSet(['BINARY_SUBSCR'], get_united_element))


class TypeSuperTuple(TypeSuperContainer):
    implemented_types = ('tuple',)
    cont_class = TypeTuple



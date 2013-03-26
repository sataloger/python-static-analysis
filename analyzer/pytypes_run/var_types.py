# -*- coding: utf-8 -*-

import sys
import itertools
from random import randint
from copy import copy, deepcopy
from opcode import opname
from itertools import *
from pytypes_run.var_operations import *
from pytypes_run.base_classes import *
from pytypes_run.type_classes import *
from pytypes_run.type_callable import TypeFunction, TypeGenerator, TypeModule, TypePackage, TypeBuiltinFunction, TypeBuiltinSmthCallable
from pytypes_run.type_class import TypeSuperObject, TypeSuperMetaClass, TypeSymTable, TypeClassMethod
from pytypes_run.type_tuple import TypeTuple, TypeSuperContainer, TypeSuperTuple
from pytypes_run.type_list import TypeList, TypeSuperList
from pytypes_run.type_dict import TypeDict, TypeSuperDict
from pytypes_run.type_unknown import TypeUnknown

#import binascii
from analyzer.pytypes_run.base_classes import BaseInfoStorage
from analyzer.pytypes_run.type_classes import TypeSimple
from analyzer.pytypes_run.var_operations import VAR_INSTS
from my_serialize import fcode_to_uniq, mcode_to_uniq, pcode_to_uniq


# можно для каждого возможного типа запоминать, сколько раз переменная была этого типа
class VarTypes(BaseInfoStorage):
    insts_handler = deepcopy(BaseInfoStorage.insts_handler)
    implemented_insts = insts_handler.stored_insts

    containers_maxlen = 10
    containers_maxname = 'unknown'
    containers = ['TypeSuperTuple', 'TypeSuperList', 'TypeSuperDict']
    iterable = containers + ['TypeIterator', 'TypeGeneratorObject']
    callable = ('TypeFunction', 'TypeGenerator', 'TypeBuiltinFunction', 'TypeBuiltinSmthCallable',
            'TypeSuperObject', 'TypeClassMethod', 'TypeSuperMetaClass', 'TypeUnknown')
    callable_wo_unknown = set(callable) - set(['TypeUnknown'])

    types_classes = {}
    types_classes_by_real_name = {}
    for typecls in (TypeSimple, TypeSlice,
                    TypeSuperTuple, TypeSuperDict, TypeSuperList,
                    TypeIterator, TypeGeneratorObject, TypeUnknown, TypeCode,
                    TypeFunction, TypeGenerator, TypeModule, TypePackage,
                    TypeSuperObject, TypeSuperMetaClass, TypeClassMethod, TypeSymTable,
                    TypeBuiltinFunction, TypeBuiltinSmthCallable):
        types_classes_by_real_name[typecls.__name__] = typecls
        for tpname in typecls.implemented_types:
            types_classes[tpname] = typecls

    def __init__(self, init_types=None, init_consts=None,
                 containers_maxlen=None, init_types_constructor_kwargs=None):
        BaseInfoStorage.__init__(self)
        if containers_maxlen is not None:
            self.containers_maxlen = containers_maxlen
        self.types = {}

        if init_types is not None:
            for pair in init_types.items():
                if init_types_constructor_kwargs is not None:
                    self.add_type(constructor_kwargs=init_types_constructor_kwargs.get(pair[0]), *pair)
                else:
                    self.add_type(*pair)


        if init_consts is not None:
            for const in init_consts:
                self.add_type_from_const(const)
        self.redirected_insts = VAR_INSTS


    def _repr_inner(self):
        res_lst = [repr(curtype) for curtype in self.types.values()]
        return 'VarTypes{' + ', '.join(res_lst) + '}'


    def _pretty_inner(self):
        res_lst = [repr(curtype) for curtype in self.types.values()]
        return ', '.join(res_lst)

    _show_dublicates = _pretty_inner

    def _list_names(self):
        res = set()
        for curtype in self.types.values():
            res.update(curtype._list_names())
        return res

    def __deepcopy__(self, memo):
        res = self.__class__(containers_maxlen=self.containers_maxlen)
        res.types = deepcopy(self.types)
        return res


    @staticmethod
    def get_class(typename):
        if typename in VarTypes.types_classes:
            return VarTypes.types_classes[typename]
        else:
            raise Exception('Found unsupported type: %r' % typename)

    @staticmethod
    def _get_class_by_real_name(typename_cls):
        if typename_cls in VarTypes.types_classes_by_real_name:
            return VarTypes.types_classes_by_real_name[typename_cls]
        else:
            raise Exception('Found unsupported type class: %r' % typename_cls)

#    @staticmethod
#    def typeobj_to_name(typeobj):
#        if typeobj.implemented_types:
#            return VarTypes.get_class_typename(typeobj.implemented_types[0])
##        if len(typeobj.implemented_types) == 1:
##            typename = typeobj.implemented_types[0]
##        elif 'int' in typeobj.implemented_types:
##            typename = 'simple'
#        else:
#            raise Exception('Unknown typeobj: %r' % typeobj)
##        return typename

    def add_typeobj(self, typeobj):
        tpname_cls = typeobj.__class__.__name__
        if tpname_cls not in VarTypes.types_classes_by_real_name:
            typename_cls = VarTypes._get_class_by_real_name(
                                       VarTypes.get_class(tpname_cls))
        self._try_add_type_class_by_cls(tpname_cls)
        self.types[tpname_cls] |= typeobj


    @staticmethod
    def get_class_typename(typename):
        return VarTypes.types_classes[typename].__name__

    def _try_add_type_class_by_cls(self, typename_cls, constructor_kwargs={}):
        if typename_cls not in self.types:
            if typename_cls in self.containers:
                self.types[typename_cls] = self._get_class_by_real_name(typename_cls)(
                      self.containers_maxlen, self.containers_maxname, **constructor_kwargs)
            else:
                self.types[typename_cls] = self._get_class_by_real_name(typename_cls)(**constructor_kwargs)

    def try_add_type_class(self, typename, constructor_kwargs):
        typename_cls = self.get_class_typename(get_typename(typename))
        self._try_add_type_class_by_cls(typename_cls, constructor_kwargs)

    def add_type(self, typename, value, from_const=False, constructor_kwargs={}):
        self.try_add_type_class(typename, constructor_kwargs)
        typename_cls = self.get_class_typename(typename)
        if typename_cls == 'TypeSimple':
            if from_const:
                self.types[typename_cls].add_const(value)
            else:
                self.types[typename_cls].add_typename(typename)
        else:
            self.types[typename_cls] |= value

    def add_type_from_const(self, const):
        tpname = get_typename(type(const).__name__)
        self.add_type(tpname, const, from_const=True)

    def clear(self):
        self.types = {}

    def __nonzero__(self):
        return any(typeobj for typeobj in self.types.values())

    def _lge_inner(self, other):
        all_keys = set(self.types.keys()) | set(other.types.keys())
        lge_list = []
        for curkey in all_keys:
            if curkey in self.types:
                if curkey not in other.types:
                    lge_list.append((0, 1, 0))
                else:
                    lge_list.append(self.types[curkey].lge(other.types[curkey]))
            else:
                if curkey in other.types:
                    lge_list.append((1, 0, 0))
                else:
                    lge_list.append((0, 0, 1))
                    raise Exception('Impossible situation')
        if lge_list:
            if len(lge_list) > 1:
                return map(all, map(None, *lge_list))
            else:
                return lge_list[0]
        else:
            return (0, 0, 1)

    def __ior__(self, other):
        for typename_cls in other.types:
            self._try_add_type_class_by_cls(typename_cls)
#            print "types: %r \n\t self : %r\n\tother : %r "% (typename_cls,self.types[typename_cls], other.types[typename_cls])
            self.types[typename_cls] |= other.types[typename_cls]
        return self

    def __or__(self, other):
        res = self.__class__()
        res.__ior__(other)
        return res

    def __div__(self, other):
        res = self.__class__()
        return res
#        for typename in self.types:
#            if self.types[typename] is not None:
#                continue
#            if other.types[typename] is None:
#                res.types[typename] = deepcopy(self.types[typename])
#            else:
#                res.types[typename] = self.types[typename] / other.types[typename]

    def get_containers(self):
        return [self.types[typename] for typename in self.containers
                                         if typename in self.types]

    def to_list(self):
        res = create_empty()
        has_smth = False
        if 'TypeSuperList' in self.types:
            lst_obj = deepcopy(self.types['TypeSuperList'])
            has_smth = True
        else:
            lst_obj = self._get_class_by_real_name('TypeSuperList')(self.containers_maxlen, self.containers_maxname)
        if 'TypeSuperTuple' in self.types:
            has_smth = True
            for tpl in self.types['TypeSuperTuple'].values.values():
                l_name = lst_obj.try_add_cont(tpl.length)
                lst_obj.values[l_name].add_type(tpl)

        if 'TypeIterator' in self.types:
            has_smth = True
            l_one = TypeList(self.containers_maxlen, self.containers_maxname)
            l_one.create_from_iterable(self.types['TypeIterator'])
            l_name = lst_obj.try_add_cont(l_one.length)
            lst_obj.values[l_name] |= l_one

        if not has_smth:
            l_one = TypeList(self.containers_maxlen, self.containers_maxname)
            l_one.add_const(None)
            l_one.fix_length(self.containers_maxname)
            l_name = lst_obj.try_add_cont(l_one.length)
            lst_obj.values[l_name] |= l_one
            print "Warning: trying convert VarTypes to list w/o having containers." 

        res.types['TypeSuperList'] = lst_obj
        return res

    def is_multiple_res(self, inst):
        if opname[inst[1]] in ('UNPACK_SEQUENCE', ):
            return inst[2]
        else:
            return None

    def handle_inst_rd(self, inst_name, inst, vars, **kwargs):
        assert all(isinstance(arg["types"], VarTypes) for arg in vars)

        mult_size = self.is_multiple_res(inst)
        if inst_name not in INPLACE_INSTS:
            if mult_size is None:
                res = {"types":create_empty()}
            else:
                res = {"types": [create_empty() for i in range(mult_size)]}

        if 'inst_name' not in kwargs:
            kwargs['inst_name'] = inst_name
        if 'inst' not in kwargs:
            kwargs['inst'] = inst
        all_typenames = set(self.types.keys())
#        for varobj in vars:
#            all_typenames.update(varobj.types.keys())
        for typename in all_typenames:
            if typename in self.types:
                if self.types[typename].implement_inst(inst_name):
                    kwargs['self_obj'] = self.types[typename]
                    # instructions that need VarTypes as theirs args
                    if inst_name in INSTS_GET_VARTYPES:
                        inst_res = self.types[typename].handle_inst(vars=vars, **kwargs)

                    else:
                        inst_res = self.types[typename].handle_inst(vars=map(lambda varobj: {"types": varobj["types"].types.get(typename)}, vars), **kwargs)

                    if inst_res is not None:
                        inst_res = inst_res["types"]

                    if inst_name in INPLACE_INSTS:
                        continue

                    if isinstance(inst_res, VarTypes):
                        res["types"] |= inst_res
                    elif mult_size:
                        assert len(res["types"]) == len(inst_res)
                        for rv, v in map(None, res["types"], inst_res):
                            rv |= v
                    elif inst_res is not None:
                        res["types"].add_typeobj(inst_res)
                #else:
                    #raise NotImplementedError("%s doesn't implement instruction %r" % \
                             #(self.__class__.__name__, inst_name))
        if inst_name in INPLACE_INSTS:
            return {"types": self}
        else:
            return res

    def __inst_compare(self):
        return {"types":VarTypes(init_types={'bool':None})}

    def bool_insts(self, inst, vars):
        res = {"types":deepcopy(self)}
        for var in vars:
            res["types"] |= var["types"]
        return res

    def get_iter(self, inst, tp_cls=TypeIterator):
        tp_str = tp_cls.implemented_types[0]
        tp_name = tp_cls.__name__
        res = {"types": VarTypes(init_types={tp_str: ()})}
        for typename in self.types:
            if typename in VarTypes.iterable:
                res["types"].types[tp_name] |= self.types[typename]
        if 'TypeUnknown' in self.types:
            res["types"].types[tp_name].values.add('unknown')
        if 'TypeSimple' in self.types:
            res["types"].types[tp_name].values.update(self.types['TypeSimple'].get_iter())
        if not len(res["types"].types[tp_name].values):
            print "Warning: trying to iterate over non-iterable types: %r!" % self
            res["types"].types[tp_name].values.add('unknown')
        return res

    @staticmethod
    def build_tuple(vars):
        res = create_empty()
        tpname = VarTypes.get_class_typename(get_const_typename(()))
        res.types[tpname] = VarTypes.types_classes_by_real_name[tpname](VarTypes.containers_maxlen, VarTypes.containers_maxname)
        res.types[tpname].build(vars)
        return res

    @staticmethod
    def build_list(vars):
        res = create_empty()
        tpname = VarTypes.get_class_typename(get_const_typename([]))
        res.types[tpname] = VarTypes.types_classes_by_real_name[tpname](VarTypes.containers_maxlen, VarTypes.containers_maxname)
        res.types[tpname].build(vars)
        return res

    @staticmethod
    def build_dict(inst):
        res = create_empty()
        tpname = VarTypes.get_class_typename(get_const_typename({}))
        res.types[tpname] = VarTypes.types_classes_by_real_name[tpname](VarTypes.containers_maxlen, VarTypes.containers_maxname)
        res.types[tpname].build(inst)
        return res

    @staticmethod
    def build_slice(vars):
        res = create_empty()
        tpname = VarTypes.get_class_typename(get_const_typename(slice(0)))
        res.types[tpname] = VarTypes.types_classes_by_real_name[tpname](*vars)
        return res

    @staticmethod
    def build_class(vars):
        res = create_empty()
        tpname = 'TypeSuperMetaClass'
        res.types[tpname] = TypeSuperMetaClass.build(vars, res)
        return res


    def _pickle(self):
        def _get_set(tp):
            res = set()
            for tpl in tp.values.values():
                for names in tpl.values:
                    for name in names:
                        res.add(name)
            return res
        def _get_set_values(tp):
            res = set()
            for tpl in tp.values.values():
                for names in tpl.values.values():
                    for name in names:
                        res.add(name)
            return res

        res = {}
        for tn, tp in self.types.items():
            if tn == 'TypeSimple':
                for name in tp.stored_types:
                    res[name] = None
            elif tn in self.containers:
                res[tp.implemented_types[0]] = {'len': 'unknown',
                                                'items': _get_set(tp)}
                if tn == 'TypeSuperDict':
                    res[tp.implemented_types[0]]['values'] = _get_set_values(tp)
            elif isinstance(tp, TypeSuperObject):
                attrs = {}
                res['::other'] = {tp.implemented_types[0]: attrs}
            elif tn in ('TypeFunction', 'TypeModule', 'TypePackage'):
                if tn == 'TypeFunction' and tp.cfgs:
                    descr = fcode_to_uniq(tp.cfgs.values()[0].codeobj)
#                    print "GOT_FUNCTION:", descr
                elif tn == 'TypeModule' and tp.module:
                    descr = mcode_to_uniq(tp.module.top.codeobj)
#                    print "GOT_MODULE:", descr
                elif tn == 'TypePackage' and tp.module:
                    descr = pcode_to_uniq(tp.module.top.codeobj)
#                    print "GOT_PACKAGE:", descr
                else:
                    descr = None
                res[tp.implemented_types[0]] = descr
            elif isinstance(tp, TypeUnknown):
                res[tp.implemented_types[0]] = None
            else:
                res['::other'] = {tp.implemented_types[0]: None}
        return res

    def unary_convert(self):
        return {"types": create_unknown()}


    insts_handler.add_set(InstSet(['COMPARE_OP', 'UNARY_NOT'],
                                  __inst_compare))
    insts_handler.add_set(InstSet(['UNARY_CONVERT'], unary_convert))
    insts_handler.add_set(InstSet(['BINARY_AND', 'BINARY_OR',
         'BINARY_XOR', 'INPLACE_AND', 'INPLACE_OR', 'INPLACE_XOR'], bool_insts))
    insts_handler.add_set(InstSet(['GET_ITER'], get_iter))


def create_unknown():
    return VarTypes(init_types={'unknown': None})

def create_undef():
    return VarTypes(init_types={'undef': None})

def create_empty():
    return VarTypes()

setglobal('VarTypes', VarTypes)
setglobal('create_unknown', create_unknown)
setglobal('create_undef', create_undef)
setglobal('create_empty', create_empty)



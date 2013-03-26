# -*- coding: utf-8 -*-

from copy import copy, deepcopy
from itertools import *
from pytypes_run.var_operations import *
from pytypes_run.base_classes import *
from pytypes_run.type_unknown import ParentType
from pytypes_run.type_callable import TypeCallable, TypeFunction
from pytypes_run.type_baseobject import TypeBaseObject


class TypeBaseSuper(ParentType):
    implemented_types = ('::inner_super',)
    insts_handler = deepcopy(ParentType.insts_handler)
    implemented_insts = insts_handler.stored_insts

    def __init__(self):
        self.values = {}
        self.attrs = {}

    def add_type(self, other):
        intersect = set(self.values) & set(other.values)
        diff = set(other.values) - set(self.values)
        for name in intersect:
            self.values[name] |= other.values[name]
        for name in diff:
            self.values[name] = other.values[name]
        self.add_type_attrs(other)

    def add_one(self, one):
        if one.name in self.values:
            self.values[one.name] |= one
        else:
            self.values[one.name] = one

    def __deepcopy__(self, memo):
        res = self.__class__()
        res.values = deepcopy(self.values)
        res.attrs = deepcopy(self.attrs)
        return res

    def _repr_inner(self):
        res_lst = []
        for name, one in self.values.items():
            res_lst.append("%s: %r" % (name, one))
        return ('%s([' % self.clsname)+ '], ['.join(res_lst) + '])'

    def _pretty_inner(self):
        res_lst = []
        for name, one in self.values.items():
            res_lst.append("%r" % one)
        return ('%s(' % self.implemented_types[0])+ ', '.join(res_lst) + ')'
    _show_dublicates = _pretty_inner

    def _list_names(self):
        res = set()
        for name, one in self.values.items():
            res.update(one._list_names())
        return res

    def clear(self):
        self.values.clear()

    def __nonzero__(self):
        return len(self.values)

    def store_attr(self, inst, vars):
        for v in self.values.values():
            v.store_attr(inst, vars)

    def delete_attr(self, inst):
        for v in self.values.values():
            v.delete_attr(inst)

    def load_attr(self, inst):
        if not self.values:
            return {"types":create_unknown()}
        else:
            res = {"types":create_empty()}
            for v in self.values.values():
                res["types"] |= v.load_attr(inst)["types"]
#            print "LOAD_ATTR: %r" % res
            return res

    def _lge_inner_attr(self, other):
        sa = set(self.attrs.keys())
        oa = set(other.attrs.keys())
        lge_list = [self.attrs[name].lge(other.attrs[name]) 
                    for name in sa & oa]
        if lge_list:
            if len(lge_list) > 1:
                lge_united = map(all, map(None, *lge_list))
            else:
                lge_united = lge_list[0]
        else:
            lge_united = (1, 1, 1)
        less = int(sa <= oa and lge_united[0])
        greater = int(sa >= oa and lge_united[1])
        equal = int(sa == oa and lge_united[2])
        print self, other, (less, greater, equal)
        return (less, greater, equal)

    def add_type_attrs(self, other):
        if self.__class__ != other.__class__:
            print "Warning: adding type to object: %r" % other
        # FIXME
        sa = set(self.attrs.keys())
        oa = set(other.attrs.keys())
        for name in sa & oa:
            self.attrs[name] |= other.attrs[name]
        for name in oa - sa:
            self.attrs[name] = other.attrs[name]

    def _lge_inner(self, other):
        return (0,0,1)

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

    insts_handler.add_set(InstSet(['STORE_ATTR'], store_attr))
    insts_handler.add_set(InstSet(['LOAD_ATTR'], load_attr))
    insts_handler.add_set(InstSet(['DELETE_ATTR'], delete_attr))


class TypeObject(ParentType):
    implemented_types = ('::inner_object',)
    insts_handler = deepcopy(ParentType.insts_handler)
    implemented_insts = insts_handler.stored_insts

    def __init__(self, name=None, meta_parent=None, initial_args=None):
        ParentType.__init__(self)
        self.name = name
        self.meta_parent = meta_parent
        
        if name is not None:
            self.call_init(*initial_args)

    def __deepcopy__(self, memo):
        res = self.__class__(self.name, self.meta_parent)
        return res
    
    def add_type(self, other):
        self.name = other.name
        self.meta_parent = other.meta_parent

    # this should call object's __init__()
    def call_init(self, from_inst_num, func_args):
        if '__init__' in self.meta_parent["types"].attrs:
            vinit = self.meta_parent["types"].attrs['__init__']
            if 'TypeClassMethod' in vinit["types"].types:
                vinit["types"].types['TypeClassMethod'].call(from_inst_num, func_args)

    # this is working like single proxy
    def call_func(self, inst, specInfo):
        if '__call__' in self.meta_parent["types"].attrs:
            return self.meta_parent.attrs['__call__'].handle_inst_rd(inst[1], inst, (),
                    specInfo=specInfo, no_push=True)
        else:
            return {"types":create_unknown()}


    def _repr_inner(self):
        return ('%s(' % self.clsname) + \
                ';\t'.join([ "%s:%r" % (name, attr)
                           for name, attr in self.meta_parent["types"].attrs.items()]) + ')'

    def _pretty_inner(self):
        return ('%s_obj(' % self.name) + \
                ';\t'.join([ "%s:%r" % (name, attr)
                           for name, attr in self.meta_parent["types"].attrs.items()]) + ')'

    def _show_dublicates(self):
        return ('%s_obj(' % self.name) + \
                ', '.join(["%s" % name for name in self.meta_parent["types"].attrs]) + ')'

    def store_attr(self, inst, vars):
        attrname = smtbl.get_varname_by_id(inst[2])
        if attrname in self.meta_parent["types"].attrs:
            self.meta_parent["types"].attrs[attrname] |= vars[0]
        else:
            self.meta_parent["types"].attrs[attrname] = vars[0]
#        print (inst[0], "STORE_ATTR", attrname), self, vars

    def delete_attr(self, inst):
        attrname = smtbl.get_varname_by_id(inst[2])
        if attrname in self.meta_parent["types"].attrs:
            pass
#            del self.attrs[attrname]
        else:
            print "Warning: trying to delete attribute %r from %r" % (attrname, self.meta_parent)

    def load_attr(self, inst):
        attrname = smtbl.get_varname_by_id(inst[2])
        if attrname in self.meta_parent["types"].attrs:
            return self.meta_parent["types"].attrs[attrname]
        else:
            print "Warning: trying to load attribute %r from %r" % (attrname, self.meta_parent)
            return {"types":create_unknown()}

    insts_handler.add_set(InstSet(['STORE_ATTR'], store_attr))
    insts_handler.add_set(InstSet(['LOAD_ATTR'], load_attr))
    insts_handler.add_set(InstSet(['DELETE_ATTR'], delete_attr))


class TypeSuperObject(TypeCallable, TypeBaseSuper):
    implemented_types = ('::object',)
    insts_handler = deepcopy(TypeCallable.insts_handler)
    insts_handler.update(TypeBaseSuper.insts_handler)
    implemented_insts = insts_handler.stored_insts

    _repr_inner = TypeBaseSuper._repr_inner
    _lge_inner = TypeBaseSuper._lge_inner
    _list_names = TypeBaseSuper._list_names

    def __init__(self, vparent=None, meta_parent=None):
        TypeCallable.__init__(self)
        TypeBaseSuper.__init__(self)
        self.vparent = vparent
        self.meta_parent = meta_parent

    def _pretty_inner(self):
        res_lst = []
        for name, one in self.values.items():
            res_lst.append("%r" % one)
        return ('object(' + ', '.join(res_lst) + ')')

    _show_dublicates = _pretty_inner

    def add_type(self, other):
        for p_cls in (TypeCallable, TypeBaseSuper):
            p_cls.add_type(self, other)

        self.vparent = other.vparent
        self.meta_parent = other.meta_parent

    # this is working like multiproxy
    def call_func(self, inst, specInfo, no_push=False):
        res["types"] = create_empty()
        for name, v in self.values.items():
            res["types"] |= v.call_func(inst, specInfo)
        if no_push:
            return res
        else:
            stack.push_var(res)

#    @staticmethod
#    def create_superobject(name, symtable, vparent):
#        res = TypeSuperObject(vparent)
#        res.values[name] = TypeObject.create_object(name, symtable, vparent)
#        return res

    insts_handler.add_set(InstSet(['CALL_FUNCTION', 'CALL_FUNCTION_VAR',
         'CALL_FUNCTION_KW', 'CALL_FUNCTION_VAR_KW'], call_func))

# stub for classes
class TypeSymTable(ParentType):
    implemented_types = ('::inner_symtable',)
    insts_handler = deepcopy(ParentType.insts_handler)
    implemented_insts = insts_handler.stored_insts

    def __init__(self, _smtbl=None, code=None):
        ParentType.__init__(self)
        self.smtbl = _smtbl
        self.owner_code = code

    def __deepcopy__(self, memo):
        res = self.__class__()
        res.smtbl = self.smtbl._hardcopy()
        res.owner_code = self.owner_code
        return res

    def add_type(self, other):
        if self.smtbl is None:
            if other.smtbl is not None:
                self.smtbl = other.smtbl._hardcopy()
        elif other.smtbl is not None:
            self.smtbl |= other.smtbl
        
        # FIXME: quick hack
        if other.owner_code != None:
            self.owner_code = other.owner_code

    def _repr_inner(self):
#        return ('%r' % self.smtbl).replace('\n', ' ')
        return ('%r' % self.smtbl)
    _pretty_inner = _repr_inner

class TypeClassMethod(TypeFunction):
    implemented_types = ('classmethod',)
    insts_handler = deepcopy(TypeFunction.insts_handler)
    implemented_insts = insts_handler.stored_insts

    def __init__(self, mclsdict=None):
        TypeFunction.__init__(self)
        self.mclsdict = copy(mclsdict)

    def __deepcopy__(self, memo):
        res = TypeFunction.__deepcopy__(self, memo)
        res.mclsdict = copy(self.mclsdict)
        return res

    def create_from(self, other):
        TypeFunction.create_from(self, other)
        self.mclsdict = copy(other.mclsdict)

    def add_type(self, other):
        TypeFunction.add_type(self, other)
        if self.mclsdict is not None:
            if other.mclsdict is not None:
                self.mclsdict.update(other.mclsdict)
        else:
            self.mclsdict = copy(other.mclsdict)

#    def store_call_result(self, cfgmclsdict, code, inst_num):
#        call_table[(code, inst_num)] = cfgmclsdict.bbs['exit'].states.states['normal'].stack.vars[-1]

    def _get_parent_smtbl(self, code, cfg):
#        print "PARENT_SMTBL: %r" % self.mclsdict[parent_code[code]]
        return self.mclsdict[parent_code[code]][0]

    def _change_func_args(self, code, func_args):
        if func_args is None:
            res = {'params': [{"types":self.mclsdict[parent_code[code]][1]}]}
        else:
            res = copy(func_args)
            res_params = copy(res['params'])
            res_params.insert(0, {"types": self.mclsdict[parent_code[code]][1]})
            res['params'] = res_params
        return res

    def call(self, from_inst_num, func_args=None):
#        print "CALLING METHOD for mclsdictid: %r"  % id(self.mclsdict)
        return TypeFunction.call(self, from_inst_num, func_args)

    @staticmethod
    def build(basefunc, mclsdict):
        res = TypeClassMethod(mclsdict)
        res.init_from(basefunc)
        return res

class TypeMetaClass(TypeBaseObject):
    implemented_types = ('::inner_metaclass_one',)
    insts_handler = deepcopy(TypeBaseObject.insts_handler)
    implemented_insts = insts_handler.stored_insts

    def __init__(self, name=None, symtable=None, parents=None, code=None,
            vparent=None):
        ParentType.__init__(self)
        self.name = name
        self.symtable = symtable
        self.parents = parents
        self.code = code
        self.vparent = vparent
#        print "GOT for %s:" % self.clsname, (name, symtable, parents)
        if name is not None:
            self.attrs = symtable.globals
            self._build_methods()

    def __deepcopy__(self, memo):
        res = self.__class__(self.name. self.symtable, self.parents, self.code, self.vparent)
        return res

    def _build_methods(self):
        mclsdict = {self.code: (self.symtable, self.vparent)}
        for v in self.attrs.values():
            if 'TypeFunction' in v["types"].types:
                v["types"].types['TypeClassMethod'] = TypeClassMethod.build(v["types"].types['TypeFunction'], mclsdict)
                del v["types"].types['TypeFunction']

    def _repr_inner(self):
        return ('%s(' % self.clsname) + \
                ';\t'.join([ "%s:%r" % (name, attr)
                           for name, attr in self.attrs.items()]) + ')'

    def _pretty_inner(self):
        return ('%s_obj(' % self.name) + \
                ';\t'.join([ "%s:%r" % (name, attr)
                           for name, attr in self.attrs.items()]) + ')'
    _show_dublicates = _pretty_inner

#    def _repr_inner(self):
#        return '%s(%s)' % (self.clsname, self.name)
#
#    def _pretty_inner(self):
#        return '%s' % self.name

    def call(self, from_inst_num, func_args=None):
        meta_parent = {"types":self}
        return {"types":TypeObject(self.name, meta_parent, [from_inst_num, func_args])}

class TypeSuperMetaClass(TypeCallable, TypeBaseSuper):
    implemented_types = ('metaclass',)
    insts_handler = deepcopy(TypeCallable.insts_handler)
    insts_handler.update(TypeBaseSuper.insts_handler)
    implemented_insts = insts_handler.stored_insts

    _repr_inner = TypeBaseSuper._repr_inner
    _pretty_inner = TypeBaseSuper._pretty_inner
    _lge_inner = TypeBaseSuper._lge_inner
    _list_names = TypeBaseSuper._list_names

    def __init__(self):
        TypeCallable.__init__(self)
        TypeBaseSuper.__init__(self)
    
#    def create(self, value):
#        tmp_cont = self.cont_class(self.maxlen, self.maxlen_name)
#        tmp_cont.create(value)
#        self.values = {tmp_cont.length:tmp_cont}

    def add_type(self, other):
        for p_cls in (TypeCallable, TypeBaseSuper):
            p_cls.add_type(self, other)

    def add_const(self, const):
#        raise Exception("ADDING CONST to %r: %r" % (self.clsname, const))
        return
        self.values[cur_name] |= const

    def call(self, from_inst_num, func_args=None):
        if not self.values:
            return {"types" : create_unknown()}
        else:
            vparent = {"types" : create_empty()}
#            print "CALLING METACONSTRUCTOR, objid: %r" % id(vparent)
            vparent["types"].types['TypeSuperObject'] = TypeSuperObject(vparent["types"])
            for name, v in self.values.items():
                vparent["types"].types['TypeSuperObject'].add_one(v.call(from_inst_num, func_args)["types"])
            return vparent

    @staticmethod
    def build(vars, vparent):
        # class params always has to be stored like this:
        res = TypeSuperMetaClass()
        symtable = vars[0]["types"].types['TypeSymTable'].smtbl
        code = vars[0]["types"].types['TypeSymTable'].owner_code
        parents = vars[1]["types"]
        name = vars[2]["types"].types['TypeSimple']._last_const['str']
        mclass = TypeMetaClass(name, symtable, parents, code, vparent)
        res.values = {name: mclass}
#        print "BUILD_RES: %r" % res
        return res

#    insts_handler.add_set(InstSet(['BINARY_ADD', 'INPLACE_ADD'], add))


# -*- coding: utf-8 -*-

import sys
import os
import re
import itertools

import var_aliases
import var_values

from random import randint
from copy import copy, deepcopy
from collections import deque
from itertools import *
from opcode import opname
from byteplay import *

from pytypes_run.base_classes import *
from pytypes_run.type_unknown import ParentType, TypeUnknown
from analyzer.pytypes_run.base_classes import BaseInfoStorage
from pytypes_run.var_values import MyValues

class SymbolTable(BaseInfoStorage):
    insts_handler = deepcopy(BaseInfoStorage.insts_handler)
    implemented_insts = insts_handler.stored_insts

    def __init__(self, **kwargs):
        BaseInfoStorage.__init__(self)
        self.locals = {}
        self.local_names = []
        self.globals = {}
        self.global_names = []
        self.cell_free_vars = {}
        self.cell_names = []
        self.free_names = []
        self.cell_free_names = []
        self.consts = {}
        self.parent = None
        self.bb_processed = False
        
        # creating from __deepcopy__
        if not len(kwargs):
            return

        smtbl_args = kwargs['smtbl_args']
        self.arg_count = smtbl_args['arg_count']
        self.cfg = smtbl_args['cfg']

        try:
            prefix = self.cfg.prefix
        except KeyError:
            prefix = None
        self.alias_store = AliasStorage(prefix)

#        print "smtbl_args.get('func_args')"
#        from pprint import pprint
#        pprint(smtbl_args)
        self._aso = kwargs['_aso']

        # local variables initializer
        unkn_or_empty = kwargs['entry_bb'] and create_unknown or create_empty
        unkn_or_empty_value = kwargs['entry_bb'] and create_unknown_value or create_empty_value

        if kwargs['entry_bb']:
            self.bb_processed = True
            
        if smtbl_args['vars'] is not None:
            
            self.set_var_names(*smtbl_args['vars'])
            if 'parent' in smtbl_args:
                self.set_parent(smtbl_args['parent'], unkn_or_empty, unkn_or_empty_value)
            else:
                self.set_parent(None, unkn_or_empty, unkn_or_empty_value)
            if not kwargs['exit_bb']:
                self._set_local_vars(unkn_or_empty, unkn_or_empty_value, smtbl_args.get('func_args'))
            else:
                self.locals.clear()
                for name in self.local_names:
                    self.alias_store.addVar(name, self.cfg.prefix, getabspath(self.cfg.codeobj.co_filename))
                    self.locals[name] = {"types":unkn_or_empty( "types" ),"aliases":create_empty_alias(name, self.cfg.prefix),"values":unkn_or_empty_value()}

        if smtbl_args['consts'] is not None:
            self.set_consts(smtbl_args['consts'])

        self._update_aso()
#        print "ASO(%r): %r" % (id(self), self._aso)

    def get_ids(self):
        ls = set([id(v) for v in self.locals.values()])
        return ls
#        cfs = set([id(v) for v in self.cell_free_vars.values()])
#        return ls | cfs

    def get_id_vars(self):
        res = {}
        for v in self.locals.values():
            res[id(v)] = v
        return res

    def get_id_names(self):
        res = {}
        for k, v in self.locals.items():
            res[id(v)] = k
        return res

    def get_items_by_names(self, names):
        res = {}
        for name in names:
            res[name] = self.locals[name]
        return res

    def __deepcopy__(self, memo):
        res = self.__class__()
        res.cfg = self.cfg
        res.parent = self.parent
        res.arg_count = self.arg_count
        res.global_names = self.global_names
        res.local_names = self.local_names
        res.cell_names = self.cell_names
        res.free_names = self.free_names
        res.cell_free_names = self.cell_free_names
        res.consts = self.consts

#        if self.parent is RootSymTable:
#            res.globals = deepcopy(self.globals)
#        else:
#            res.globals = self.globals
        res.globals = copy(self.globals)

        res.cell_free_vars = self.cell_free_vars

        res._aso = _deep_aso
        res.locals = {}
#        print "DEEP_ASO_TRANS_IDS:", set(_deep_aso_trans.keys())
#        print "SELF_IDS:", self.get_ids()
#        print "LOCALS:", self.locals
        for k, v in self.locals.items():
            res.locals[k] = _deep_aso_trans[id(v)]
#        res.locals = deepcopy(self.locals)
        res.alias_store = deepcopy(self.alias_store)
        return res

    def _hardcopy(self):
#        print "CALLED HARDCOPY"
        res = self.__class__()
        res.cfg = self.cfg
        res.parent = self.parent
        res.arg_count = self.arg_count
        res.global_names = self.global_names
        res.local_names = self.local_names
        res.cell_names = self.cell_names
        res.free_names = self.free_names
        res.cell_free_names = self.cell_free_names
        res.consts = self.consts
        res.cell_free_vars = self.cell_free_vars
        res.locals = deepcopy(self.locals)
#        res = deepcopy(self)
        res.globals = deepcopy(self.globals)
        res.alias_store = deepcopy(self.alias_store)
        return res


    def set_parent(self, parent, unkn_or_empty, unkn_or_empty_value):
        # FIXME: in python we have symbol tables linking at translation, not at execution
        self.parent = parent
        if parent is None:
            raise Exception()
#            self.globals.clear()
#            for name in self.global_names:
#                self.globals[name] = unkn_or_empty()
#
#            self.cell_free_vars.clear()
#            for name_num in range(len(self.cell_free_names)):
#                self.cell_free_vars[name_num] = unkn_or_empty()
        else:
            curp = parent
            self.globals.clear()
            gleft_set = set(self.global_names)
            cfleft_set = set(range(len(self.cell_free_names)))
            while curp is not None:
                for name in copy(gleft_set):
                    if name in curp.global_names:
                        self.alias_store.addVar(name, curp.globals[name]['aliases'].varprefix, getabspath(self.cfg.codeobj.co_filename))
                        self.globals[name] = curp.globals[name]
#                        print "CHECK"
#                        print self.globals[name]
#                        print curp.globals[name]
#                        print self.alias_store.getVarAliases(name)
                        if self.alias_store.getVarAliases(name):
                            self.globals[name]['aliases'] = self.alias_store.getVarAliases(name)

                        gleft_set.discard(name)
                for i in copy(cfleft_set):
                    name = self.cell_free_names[i]
                    if name in curp.cell_free_names:
                        self.cell_free_vars[i] = curp.cell_free_vars[curp.cell_free_names.index(name)]
                        cfleft_set.discard(i)

                if gleft_set or cfleft_set:
                    while curp is not None:
                        curp = curp.parent
                        if curp and self.cfg.prefix.startswith(curp.cfg.prefix):
                            break
                else:
                    break
            gundef = []
            cfundef = []
            for name in gleft_set:
                self.alias_store.addVar(name, self.cfg.prefix, getabspath(self.cfg.codeobj.co_filename))
                self.globals[name] = {"types":unkn_or_empty( "types" ),"aliases":create_empty_alias(name,self.cfg.prefix),"values":unkn_or_empty_value()}
                gundef.append(name)
            for i in cfleft_set:
                self.cell_free_vars[i] = {"types": unkn_or_empty( "types" ), "aliases": create_empty_alias(None,None),"values":unkn_or_empty_value()}
                cfundef.append(self.cell_free_names[i])

            if cfundef:
                print 'Warning: cell_free_vars variables %r wasn\'t defined!' % cfundef
                print 'I has a parent!!: ', parent
                print 'ME(%r): ' % self.cfg.prefix, self

#            self.locals['__doc__'] = VarTypes(init_types={'NoneType':None})
            if gundef and parent is not RootSymTable:
                if '__module__' in gundef:
                    # stub for creating MetaClass global symtable
                    #TODO TEST
                    self.globals['__name__'] = {"types": VarTypes(init_types={'str':None}), "aliases": create_empty_alias('__name__',None),"values":create_empty_value()}
                    print 'gundef: %r its name: %r', gundef, gundef['__name__']
                else:
                    pass
#                    print 'Warning: global variables %r wasn\'t defined!' % gundef
#                    print 'I has a parent!!: ', parent
#                    print 'ME(%r): ' % self.cfg.prefix, self

    def set_func_args(self, func_args):
        cfg = self.cfg
        syminfo = cfg.syminfo
        lset = set()
        if syminfo.get_type() == 'function':
            real_argc = len(func_args['params'])

            theory_argc = len(syminfo.get_parameters())
            args_pos = kwargs_pos = -1

            if cfg.flags['accept_kwargs']:
                theory_argc -= 1
                kwargs_pos = theory_argc
                # preparing **kwargs arguments dict
                ### arguments pathing
                if 'kwargs' in func_args:
                    kwargs_obj = deepcopy(func_args['kwargs'])
                else:
                    kwargs_obj = {"types":VarTypes(init_types={'dict': {}}), "aliases": create_empty_alias(None,'kwargs_obj'),"values":create_empty_values()} ###TODO

            if cfg.flags['accept_args']:
                theory_argc -= 1
                args_pos = theory_argc
                # preparing *args arguments list
                if 'args' in func_args:
                    args_obj = func_args['args'].to_list()
#                    args_obj = deepcopy(func_args['args'])
                else:
                    args_obj = {"types":VarTypes(init_types={'list': []}), "aliases": create_empty_alias(None,'args_obj'),"values":create_empty_values()}

            pto_local = {}
            # NOTE : SymbolTable.get_parameters() lies to us!
            # it returns parameters not in correct order
            # FIXME : should determine order by myself
            for pid, pname in enumerate(syminfo.get_parameters()):
#                pto_local[pid] = self.local_names.index(pname)
                pto_local[pid] = pid
            
            for pid, paramobj in enumerate(func_args['params']):
                if pid >= theory_argc:
                    # filling *args arguments list
                    if cfg.flags['accept_args']:
                        args_obj["types"].types['TypeSuperList'].append(paramobj)
#                        print args_obj
                    else:
#                    print 'Error: %s calling with %i parameters, but acceping only %i' % (cfg.prefix, real_argc, theory_argc)
                        break
                else:

                    self.alias_store.addVar(self.local_names[pto_local[pid]],
                                            self.cfg.prefix, getabspath(self.cfg.codeobj.co_filename)) # addalias should be here
                    self.locals[self.local_names[pto_local[pid]]] = {'types': paramobj['types']}
                    self.locals[self.local_names[pto_local[pid]]]['aliases'] = create_empty_alias(self.local_names[pto_local[pid]],self.cfg.prefix)
                    if 'aliases' in paramobj.keys():
                        self.alias_store.addAlias(self.locals[self.local_names[pto_local[pid]]]['aliases'],paramobj['aliases'])
                        _lvar = self.locals[self.local_names[pto_local[pid]]]['aliases']
#                        raise TEST
                        self.locals[self.local_names[pto_local[pid]]]['aliases'] = self.alias_store[_lvar.varprefix+"."+ _lvar.varname]

                    self.locals[self.local_names[pto_local[pid]]]['values'] = create_empty_value();
                    #TODO TEST PARAMS
                    self.locals[self.local_names[pto_local[pid]]]['values'].unknown_value = False;
                    for value in paramobj['values'].values:  
                      self.locals[self.local_names[pto_local[pid]]]['values'].add_value(value)



                    lset.add(self.local_names[pto_local[pid]])

            lsize = len(lset)
            filled_from_args = False
            # setting up arguments from *args
            if len(lset) < theory_argc and cfg.flags['accept_args']:
                l_obj = args_obj["types"].types['TypeSuperList']
                # skipping if args is empty
                if not (len(l_obj.values) == 1 and (0 in l_obj.values)):
                    united_elem = l_obj.get_united_element()
                    filled_from_args = True
                    for pid in range(len(lset), theory_argc):
                        # not awesome approximation, but it works
                        self.locals[self.local_names[pto_local[pid]]] = deepcopy(united_elem)
                        lset.add(self.local_names[pto_local[pid]])
                        l_obj.pop()


            defp_c = len(func_args['default_params'])
            # setting up default arguments
            if not filled_from_args:
                if len(lset) < theory_argc:
                    # trick to fill only left default arguments
                    for i, pid in enumerate(reversed(range(max(len(lset), theory_argc-defp_c), theory_argc))):
                        self.locals[self.local_names[pto_local[pid]]] = func_args['default_params'][i]
                        lset.add(self.local_names[pto_local[pid]])
            else:
                if lsize < theory_argc:
                    for i, pid in enumerate(reversed(range(max(lsize, theory_argc-defp_c), theory_argc))):
                        if pto_local[pid] in lset:
                            self.locals[self.local_names[pto_local[pid]]] |= func_args['default_params'][i]
                        else:
                            self.locals[self.local_names[pto_local[pid]]] = func_args['default_params'][i]
                            lset.add(self.local_names[pto_local[pid]])

            # setting up *args arguments list
            if cfg.flags['accept_args']:
                self.locals[self.local_names[pto_local[args_pos]]] = args_obj
                lset.add(self.local_names[pto_local[args_pos]])

            # setting up **kwargs arguments dict
            if cfg.flags['accept_kwargs']:
                self.locals[self.local_names[pto_local[kwargs_pos]]] = kwargs_obj
                lset.add(self.local_names[pto_local[kwargs_pos]])

        return lset

    def set_var_names(self, global_names, local_names,
                      cell_names, free_names):
        self.global_names = list(global_names)
        self.local_names = list(local_names)
        self.cell_names = list(cell_names)
        self.free_names = list(free_names)
        self.cell_free_names = self.cell_names + self.free_names

    def _set_local_vars(self, unkn_or_empty, unkn_or_empty_value, func_args=None):
        print "Setting local vars"
        lset = set(self.local_names)
        self.locals.clear()
        if func_args is not None:
            lset.difference_update(self.set_func_args(func_args))
        for name in lset:
            self.alias_store.addVar(name, self.cfg.prefix, getabspath(self.cfg.codeobj.co_filename))
            self.locals[name] = {"types":unkn_or_empty( "types" ), "aliases": create_empty_alias(name, self.cfg.prefix),"values":unkn_or_empty_value()}
            
    def _update_aso(self):
        self._aso.update(self.get_id_vars())

    def set_consts(self, consts):
        self.consts.clear()
        for const_num in range(len(consts)):
            self.consts[const_num] = {"types":VarTypes(init_consts=consts[const_num]), "aliases": create_empty_alias(None,None),"values":MyValues([consts[const_num],False])}
            #self.consts[const_num]["values"].add_value(const_num);
            #print "!!!CONST ", const_num

    @staticmethod
    def create_root_symtable():
        bins = globals()['__builtins__']
        if isinstance(bins, dict):
            bdict = bins
        else:
            bdict = bins.__dict__
        gl_list = []
        gl_names = []
        for k, v in bdict.items():
            gl_names.append(k)
            if callable(v):
                had_type = False
                if k in ('help', 'exit', 'quit', 'license', 'exec', 'execfile', 'setattr', 'delattr'):
                    res = None
                elif k in ('input', 'eval', 'getattr', 'classmethod', 'reduce',
                        'apply', 'compile', 'min', 'max'):
#                    # FIXME: immitating TypeUnknown
#                    res = int.__long__
                    had_type = True
                    res_type = TypeUnknown()
                elif k in ('raw_input', 'copyright', 'basestring'):
                    res = ""
                elif k in ('open', 'file'):
                    # FIXME: should return file object
#                    res = int.__long__
                    had_type = True
                    res_type = TypeUnknown()
                elif k in ('reload', '__import__'):
                    had_type = True
#                    res_type = _unknown_package
                    res_type = TypeUnknown()
                else:
                    res_list = []
                    try:
                        res_list.append(v())
                    except:
                        pass
                    for arg in (1, 'a', (), (1, 2), (None, ()), (int, int), (int, '__long__'), (1,2,3,4,5)):
                        try:
                            res_list.append(v(arg))
                        except:
                            pass
                        try:
                            res_list.append(v(*arg))
                        except:
                            pass
                    if not res_list:
                        print "=====Couldn't determine type for %r!" % k
                        had_type = True
                        res_type = TypeUnknown()
                if had_type:
                    v_res = create_empty( "types" )
                    v_res.types[res_type.clsname] = deepcopy(res_type)
                else:
                    v_res = VarTypes(init_consts=res_list)
#                    tpname_res = VarTypes.get_class(get_const_typename(res)).__name__
#                    print repr(res), tpname_res
                    for tpname_res in v_res.types:
                        if tpname_res in ('TypeSuperList', 'TypeSuperTuple'):
                            # hack to change length into unknown
                            v_res.types[tpname_res] = v_res.types[tpname_res].get_slice((0, 31, None), ())["types"] # SLICE+1
                tpname = get_const_typename(v)
                if tpname != 'builtin_function_or_method':
                    tpname = 'builtin_smth_callable'
                gl_list.append(VarTypes(init_types={tpname: None},
                                        init_types_constructor_kwargs={tpname: {'name': k,
                                                                                'res_type': v_res,
                                                                                },
                                                                      }))
            else:
                gl_list.append(VarTypes(init_consts=[v]))

        class DictProxy(dict):
            def __getattr__(self, attr):
                return self[attr]

        rs = DictProxy()
        rs['stack'] = None
        rs['_aso'] = {}

        cfg = DictProxy()
        cfg['prefix'] = ''

        st = SymbolTable()
        st.global_names = gl_names
        for i, elem in enumerate(gl_list):
            st.globals[gl_names[i]] = {"types":elem, "aliases": create_empty_alias(gl_names[i],'global'),"values":create_unknown_value()}

        st.cfg = cfg
        st.parent = None
        st._aso = rs['_aso']

        rs['smtbl'] = st
                      
        setglobal('RootSymTable', st)
        setglobal('RootState', rs)
#        print st.globals['reload']
#        print st
#        exit(0)

    def __or__(self, other):
        raise NotImplementedError("Shoudn't call this")
        res = deepcopy(other)
        res.__ior__(other)
        return res

    def __comparable(self, other):
        #TODO!
        return True

    def __ior__(self, other):
        if not self.__comparable(other):
            raise Exception("Symbol table objects are incomparable: %s\n\n\n%s"
                            % (str(self), str(other)))

        sg = set(self.globals.keys())
        og = set(other.globals.keys())
        sl = set(self.locals.keys())
        ol = set(other.locals.keys())

        if self.bb_processed:
            self.alias_store |= other.alias_store
        else:
            self.alias_store = deepcopy(other.alias_store)

        for name in sg & og:
#print "Name:", name
            print "Values:", self.globals[name]
#           print "Types:",  self.globals[name]["types"]
#           print "\n"
            self.globals[name]["types"] |= other.globals[name]["types"]
            self.globals[name]["values"] |= other.globals[name]["values"]
			# duplicate result for correct bb handling

#            self.globals[name]["aliases"] = self.alias_store[self.cfg.prefix + "." + name] # raised keyerror from wwrong prefix
            self.globals[name]["aliases"] = self.alias_store.search_prefix(self.cfg.prefix, name)

        for name in og - sg:
            self.globals[name]["types"] = other.globals[name]["types"]
            self.globals[name]["values"] = other.globals[name]["values"]

#            self.globals[name]["aliases"] = self.alias_store[self.cfg.prefix + "." + name]
            self.globals[name]["aliases"] = self.alias_store.search_prefix(self.cfg.prefix, name)
        for name in sl & ol:
#            print "Var %r:\n\t%r\n\t%r" % (name,self.locals[name],other.locals[name])
            self.locals[name]["types"] |= other.locals[name]["types"]
            self.locals[name]["aliases"] = self.alias_store[self.cfg.prefix + "." + name]
            self.locals[name]["values"] |= other.locals[name]["values"]
        for name in ol - sl:
            self.locals[name]["types"] = deepcopy(other.locals[name]["types"])
            self.locals[name]["values"] = deepcopy(other.locals[name]["values"])
            self.locals[name]["aliases"] = self.alias_store[self.cfg.prefix + "." + name]
            #NOBARMENself._aso[id(self.locals[name]["types"])] = self.locals[name]
            self._aso[id(self.locals[name])] = self.locals[name]

        for var_key in self.cell_free_vars:
            self.cell_free_vars[var_key]["types"] |= other.cell_free_vars[var_key]["types"]
            self.cell_free_vars[var_key]["values"] |= other.cell_free_vars[var_key]["values"]

        self.bb_processed = other.bb_processed
        return self


    def __eq__(self, other):
        if not self.__comparable(other):
            raise Exception("Stack objects are incomparable: %s\n\n\n%s"
                            % (str(self), str(other)))

        sg = set(self.globals.keys())
        og = set(other.globals.keys())
        sl = set(self.locals.keys())
        ol = set(other.locals.keys())
        if sg != og or sl != ol:
            return False

        for var_key in self.globals:
            if self.globals[var_key] != other.globals[var_key]:
                return False
            if self.alias_store[self.cfg.prefix + "" + var_key] != other.alias_store[other.cfg.prefix + "." + var_key]:
                return False
            
        for var_key in self.locals:
            if self.locals[var_key] != other.locals[var_key]:
                return False
            if self.alias_store[self.cfg.prefix + "" + var_key] != other.alias_store[other.cfg.prefix + "." + var_key]:
                return False
            
        for var_key in self.cell_free_vars:
            if self.cell_free_vars[var_key] != other.cell_free_vars[var_key]:
                return False
        return True

    def _lge_inner(self, other):
        if not self.__comparable(other):
            raise Exception("Stack objects are incomparable: %s\n\n\n%s"
                            % (str(self), str(other)))

        sg = set(self.globals.keys())
        og = set(other.globals.keys())
        sl = set(self.locals.keys())
        ol = set(other.locals.keys())
        if sg != og or sl != ol:
            return (0, 0, 0)

        other.bb_processed = True
        
        lge_list = [self.globals[vk]["types"].lge(other.globals[vk]["types"])
                      for vk in self.globals]
        lge_list.extend([self.locals[vk]["types"].lge(other.locals[vk]["types"])
                        for vk in self.locals])
        lge_list.extend([self.globals[vk]["values"].lge(other.globals[vk]["values"]) for vk in self.globals])
        lge_list.extend([self.locals[vk]["values"].lge(other.locals[vk]["values"]) for vk in self.locals])
        
        lge_list.extend([self.cell_free_vars[vk]["types"].\
                         lge(other.cell_free_vars[vk]["types"])
                        for vk in self.cell_free_vars])
        lge_list.extend([self.alias_store.lge(other.alias_store)])
        
        if lge_list:
            if len(lge_list) > 1:
                return map(all, map(None, *lge_list))
            else:
                return lge_list[0]
        else:
            return (0,0,1)


    def _repr_inner(self):
        res = 'SymbolTable:\n\t'
        res += 'Globals:\n\t\t'
#        res += repr(self.globals) + " "
#        res += repr(self.global_names)
        res += '\n\t\t'.join(map(lambda x:
                            "%r: %r" %(x[0],x[1]),
                               self.globals.items()))
        res += '\n\tLocals:\n\t\t'
        res += '\n\t\t'.join(map(lambda x:
            "%r: %r: %r" %(id(x[1]), x[0], x[1]),
                               self.locals.items()))
        res += '\n\tAliases:'
        res += "%r" % self.alias_store
        res += '\n\tCell_Vars:\n\t\t'
        lst = []
        for i, name in enumerate(self.cell_names):
            lst.append("%r: %r" % (name, self.cell_free_vars[i]))
        res += '\n\t\t'.join(lst)

        res += '\n\tFree_Vars:\n\t\t'
        lst = []
        for i, name in enumerate(self.free_names):
            lst.append("%r: %r" % (name, self.cell_free_vars[i+len(self.cell_names)]))
        res += '\n\t\t'.join(lst)

        res += '\n'
        return res

    _pretty_inner = _repr_inner
    _show_dublicates = _pretty_inner

    def __ne__(self, other):
        return not self == other

    def load_deref(self, inst):
        return self.cell_free_vars[inst[2]]

    def store_deref(self, inst):
        name_num = inst[2]
        instNum = inst[0]
        mystats['prCount'] += 1
        varobj = stack.vars_dlt[0] 
        diff = varobj["types"] / self.cell_free_vars[name_num]["types"]
        name = self.cell_free_names[name_num]
#        if name_num < len(self.cell_names):
#            name = self.cell_names[name_num]
#        else:
#            name = self.free_names[name_num - len(self.cell_names)]
        if diff:
            self.__add_changed_type_place((instNum, name, diff))
            self.__add_for_asserts((instNum, name, varobj))

        self.cell_free_vars[name_num] = varobj


    def store_global(self, inst):
        mystats['prCount'] += 1
        name = self.global_names[inst[2]]
        instNum = inst[0]

        varobj = stack.vars_dlt[0]
        
        diff = varobj["types"] / self.globals[name]["types"]
        if diff:
            self.__add_changed_type_place((instnum, name, diff))
            self.__add_for_asserts((instnum, name, varobj))
#        self.globals[name] = varobj
        self.globals[name]["types"] = varobj["types"]
        self.globals[name]["values"] = varobj["values"]
        #self.globals[name]["types"] = varobj["types"]

        if 'aliases' in varobj:
            self.alias_store.addAlias(self.globals[name]['aliases'], varobj['aliases'] )
            self.globals[name]['aliases'] = self.alias_store.search_prefix(self.cfg.prefix, name)
        else:
            print "Warning: assigning value hasn't 'aliases' key: %r" % varobj
		

    def load_global(self, inst):
        name = self.global_names[inst[2]]
        if name not in self.globals:
            raise "WARNING: unknown global variable '%s' with number %i" % (name, inst[2])
        if mydebugDict['printWarnings']:
            if not self.globals[name]:
                print "WARNING: undefined global variable '%s' with number %i" % (name, inst[2])
        return self.globals[name]

    def load_locals(self, inst):
        # we are getting locals later at class building (from 'exit' bb)
#        return create_unknown()

        # ok, let's try pushing current smtbl into stack (stub for classes)
        return {"types":VarTypes(init_types={'::inner_symtable':None},
                                    init_types_constructor_kwargs={
                                        '::inner_symtable': {'_smtbl': smtbl, 
                                                             'code': call_stack[-1][0]},
                                    }
                       ) , "values":create_empty_value()}

    def delete_global(self, inst):
        name = self.global_names[inst[2]]
        self.alias_store.delVar(name, self.cfg.prefix, getabspath(self.cfg.codeobj.co_filename))
        self.globals[name]['aliases'] = self.alias_store[self.cfg.prefix+"."+ name]
#        self.globals[name].clear()

    def load_const(self, inst):
        return deepcopy(self.consts[inst[2]])

    def store_local(self,  inst):
        name = self.local_names[inst[2]]
        instNum = inst[0]
        mystats['prCount'] += 1
        varobj = stack.vars_dlt[0] 
        diff = varobj["types"] / self.locals[name]["types"]
        if diff:
            self.__add_changed_type_place((instNum, name, diff))
            self.__add_for_asserts((instNum, name, varobj))

        print self.locals[name]
        print varobj
#        self.locals[name] = varobj
        self.locals[name]['types'] = varobj['types']
        self.locals[name]['values'] = varobj['values']
        if 'aliases' in varobj:
            self.alias_store.addAlias(self.locals[name]['aliases'], varobj['aliases'] )
            self.locals[name]['aliases'] = self.alias_store[self.cfg.prefix+"."+ name]
        else:
            print "Warning: assigning value hasn't 'aliases' key: %r" % varobj
        
        #self.locals[name] = varobj ###
        _state._add_to_aso(varobj)

    def get_varname_by_id(self, varid):
        if varid < len(self.global_names):
            return self.global_names[varid]
        else:
            print "Warning: trying to get non-existing varname: %r from %r" % (varid, self.local_names)
            return None

    def load_local(self, inst):
        name = self.local_names[inst[2]]
        if mydebugDict['printWarnings']:
            if not self.locals[name]:
                print "WARNING: undefined local variable '%s' with number %i" \
                     % (name, inst[2])
        return self.locals[name]

    def delete_local(self, inst):
        name = self.local_names[inst[2]]
        self.alias_store.delVar(name, self.cfg.prefix, getabspath(self.cfg.codeobj.co_filename))
        self.locals[name]['aliases'] = self.alias_store[self.cfg.prefix+"."+ name]
#        self.locals[name].clear()

    def load_closure(self, inst):
        return self.cell_free_vars[inst[2]]

    def make_function(self, inst):
        res = {}
        curSt = tuple(reversed(stack.vars_dlt))
        code = curSt[0]
        if code["types"].types['TypeCode'].code.co_flags & 0x20:
            res["types"] = VarTypes(init_types={'generator': None},
                    init_types_constructor_kwargs={'generator': {'default_params_one': curSt[1:],
                                                                'code': code["types"]}
                                                  })
        else:
            res["types"] = VarTypes(init_types={'function': None},
                    init_types_constructor_kwargs={'function': {'default_params_one': curSt[1:],
                                                                'code': code["types"]}
                                                  })
        values = []
        print code
        values.append(code['values'])
        res['values'] = MyValues(init_value=[values,False])

        return res


#MAKE_CLOSURE(argc)¶
    #Creates a new function object, sets its func_closure slot, and pushes it on the stack. TOS is the code associated with the function, TOS1 the tuple containing cells for the closure’s free variables. The function also has argc default parameters, which are found below the cells.
    def make_closure(self, inst):
        curSt = tuple(reversed(stack.vars_dlt))
        code = curSt[0]
        res = {}
        if code["types"].types['TypeCode'].code.co_flags & 0x20:
            res["types"] = VarTypes(init_types={'generator': None},
                    init_types_constructor_kwargs={'generator': {'default_params_one': curSt[2:],
                                                                'freevars_one': curSt[1],
                                                                'code': code["types"]}
                                                  })
        else:
            res["types"] = VarTypes(init_types={'function': None},
                    init_types_constructor_kwargs={'function': {'default_params_one': curSt[2:],
                                                                'freevars_one': curSt[1],
                                                                'code': code["types"]}
                                                  })
        return res

    def import_star(self, inst):
        v = stack.vars_dlt[0]
        print "IMPORT_STAR AT %r: from %r" % (_state, v)
        for curtype in ('TypeModule', 'TypePackage'):
            if curtype in v["types"].types:
                m = v["types"].types[curtype]
                print "IMPORT_STAR AT %r" % m
                for name, v in m.attrs.items():
                    # 'import *' replaces all this modules globals (equals to assignment)
                    self.globals[name] = v
                if curtype == 'TypePackage':
                    path = m.names[m.last_name]
                    m_names = filter(lambda x: re.match('(.*)\.py$', x) and x != '__init__.py',
                            os.listdir(path))
                    for name in m_names:
                        m_name = name[:-3]
                        fname = os.path.join(path, name)
                        self.globals[m_name] = TypeModule.import_from_path(fname)
        print "IMPORT_STAR AT %r: %r" % (_state, inst)

    def import_name(self, inst):
        name_num = inst[2]
#        print "IMPORT_NAME %r AT %r" % (self.global_names[name_num], _state)
        stack.push_var(TypeModule.import_by_name(self.global_names[name_num], getcurpath()))
#        print stack

    def import_from(self, inst):
        newinst = (inst[0], LOAD_ATTR, inst[2])
        res = stack.vars_dlt[0]["types"].handle_inst_rd('LOAD_ATTR', inst=newinst, vars=[])
        stack.push_var(stack.vars_dlt[0])
        stack.push_var(res)

    insts_handler.add_set(InstSet(['LOAD_NAME', 'LOAD_GLOBAL'],
                                  load_global))
    insts_handler.add_set(InstSet(['STORE_NAME', 'STORE_GLOBAL'],
                                  store_global))
    insts_handler.add_set(InstSet(['DELETE_NAME', 'DELETE_GLOBAL'],
                                  delete_global))
    insts_handler.add_set(InstSet(['LOAD_CONST'], load_const))
    insts_handler.add_set(InstSet(['LOAD_FAST'], load_local))
    insts_handler.add_set(InstSet(['STORE_FAST'], store_local))
    insts_handler.add_set(InstSet(['DELETE_FAST'], delete_local))
    insts_handler.add_set(InstSet(['LOAD_DEREF'], load_deref))
    insts_handler.add_set(InstSet(['STORE_DEREF'], store_deref))
    insts_handler.add_set(InstSet(['LOAD_CLOSURE'], load_closure))
    insts_handler.add_set(InstSet(['MAKE_CLOSURE'], make_closure))
    insts_handler.add_set(InstSet(['MAKE_FUNCTION'], make_function))
    insts_handler.add_set(InstSet(['IMPORT_STAR'], import_star))
    insts_handler.add_set(InstSet(['IMPORT_NAME'], import_name))
    insts_handler.add_set(InstSet(['IMPORT_FROM'], import_from))
    insts_handler.add_set(InstSet(['LOAD_LOCALS'], load_locals))

    ###

    def compare_op(self, inst):
      return {"types":VarTypes(init_types={'bool':None}), 'values':create_unknown_value()}

# insts_handler.add_set(InstSet(['COMPARE_OP'], compare_op))

class Stacks(BaseInfoStorage):
    insts_handler = deepcopy(BaseInfoStorage.insts_handler)
    implemented_insts = insts_handler.stored_insts

    def __init__(self):
        BaseInfoStorage.__init__(self)
        self.vars = []
        self.blocks = []
        self.vars_dlt = []
        self.blocks_dlt = []

    def get_ids(self):
        return set([id(v) for v in self.vars])

    def get_id_vars(self):
        res = {}
        for v in self.vars:
            res[id(v)] = v
        return res

    def __deepcopy__(self, memo):
        res = self.__class__()
        if _deep_fix_stack:
            vars = []
            dublicates = {}
            for v in self.vars:
                id_v = id(v)
                if id_v in _deep_aso_trans:
#                    print "GOT_SHARED: %r" % id_v
                    vars.append(_deep_aso_trans[id_v])
                else:
                    if id_v in dublicates:
#                        print "GOT_DUBLICATE: %r" % id_v
                        vars.append(dublicates[id_v])
                    else:
                        new_obj = deepcopy(v)
                        vars.append(new_obj)
                        _deep_aso[id(new_obj)] = new_obj
                        dublicates[id_v] = new_obj
            res.vars = vars
        else:
            res.vars = [_deep_aso_trans[id(v)] for v in self.vars]
#        res.vars = deepcopy(self.vars)
        res.blocks = deepcopy(self.blocks)
        res.vars_dlt = deepcopy(self.vars_dlt)
        res.blocks_dlt = deepcopy(self.blocks_dlt)
        return res

    def __or__(self, other):
        raise NotImplementedError("Shoudn't call this")
        res = deepcopy(other)
        res.__ior__(other)
        return res

    def __comparable(self, other):
        if other is None:
            return False

        res = len(self.vars) != len(other.vars) or \
              len(self.blocks) != len(other.blocks) or \
              all(imap(lambda x,y:x==y, self.blocks, other.blocks))
        return res

    def __ior__(self, other):
        if not self.__comparable(other):
            raise Exception("Stack objects are incomparable: %s\n\n\n%s"
                            % (str(self), str(other)))
        for var_self, var_other in izip(self.vars, other.vars):
            var_self["types"] |= var_other["types"] 
            var_self["values"] |= var_other["values"]
            if "aliases" in var_self.keys():
                var_self["aliases"] |= var_other["aliases"]
        return self

    def __eq__(self, other):
        if not self.__comparable(other):
            raise Exception("Stack objects are incomparable: %s\n\n\n%s"
                            % (str(self), str(other)))
        return all(imap(lambda x,y: x==y, self.vars, other.vars))

    def __ne__(self, other):
        return not self == other

    def _lge_inner(self, other):
        if not self.__comparable(other):
            raise Exception("Stack objects are incomparable: 1: %r\n\n2: %r" % (self, other))
        lge_list = [sv["types"].lge(ov["types"]) for sv, ov in imap(None, self.vars,
                                                  other.vars)]
        if lge_list:
            if len(lge_list) > 1:
                return map(all, map(None, *lge_list))
            else:
                return lge_list[0]
        else:
            return (0, 0, 1)

    def _repr_inner(self):
        if len(self.vars):
            res = 'Stack(%i):\n\t%s' % (len(self.vars),
                    '\t\n'.join(map(lambda x: "%r: %r" % (id(x), x), self.vars)))
            res += "ITERATOR: %r" % self.vars[-1]["values"].iterator
        else:
            res = 'Stack(0): <empty>'
        return res

    _pretty_inner = _repr_inner
    _show_dublicates = _pretty_inner

    def pop_count(self, count):
        del self.vars_dlt[:]
        if count:
            self.vars_dlt.extend(self.vars[-count:])
            del self.vars[-count:]
        return self.vars_dlt

    def push_var(self, var):
        self.vars.append(var)

    def extend_vars(self, vars):
        self.vars.extend(vars)

    def push_var_unknown(self):
        self.vars.append({"types":create_unknown(), 'values':create_unknown_value()})

    def pop_top(self):
        self.vars_dlt = [self.vars.pop()]

    def rot_2(self):
        self.extend_vars(reversed(self.pop_count(2)))

    def rot_3(self):
        self.pop_count(3)
        self.extend_vars(self.vars_dlt[1:])
        self.push_var(self.vars_dlt[0])

    def rot_4(self):
        self.pop_count(4)
        self.extend_vars(self.vars_dlt[1:])
        self.push_var(self.vars_dlt[0])

    def dup_top(self):
        self.vars.append(self.vars[-1])

    def dup_topx(self, inst):
        self.vars.extend(self.vars[-inst[2]:])


    def push_block(self, block):
        self.blocks.append(block)

    def pop_block(self):
        tos = self.blocks.pop()
        self.pop_count(tos['vars_len'] - len(self.vars))
        self.blocks_dlt = [tos]
        return tos

    def pop_block_raising(self):
        self.blocks_dlt = []
        tos = {'type':'LOOP'}
        while tos['type'] == 'LOOP' and self.blocks:
            tos = self.blocks.pop()
            self.blocks_dlt.append(tos)
        return tos



    def setup_loop(self, inst):
        self.push_block({'type': 'LOOP',
                         'borders': (inst[0], inst[2]),
                         'vars_len': len(self.vars)})

    def setup_except(self, inst):
        self.push_block({'type': 'EXCEPT',
                         'borders': (inst[0], inst[2]),
                         'vars_len': len(self.vars)})

    def setup_finally(self, inst):
        self.push_block({'type': 'FINALLY',
                         'borders': (inst[0], inst[2]),
                         'vars_len': len(self.vars)})

    def return_to_state(self, block):
        del self.vars[block['vars_len']:]

    def break_loop(self):
        while True:
            self.pop_block()
            if self.blocks_dlt[-1]['type'] == 'LOOP':
                self.return_to_state(self.blocks_dlt[-1])
                break

    def build_insts(self, inst):
        reordered = reorder(inst, self.vars_dlt)
        if opname[inst[1]] == 'BUILD_TUPLE':
            self.vars.append({"types":VarTypes.build_tuple(reordered), 'values':create_unknown_value()})
        elif opname[inst[1]] == 'BUILD_LIST':
            self.vars.append({"types":VarTypes.build_list(reordered), 'values':create_unknown_value()})
        elif opname[inst[1]] == 'BUILD_MAP':
            self.vars.append({"types":VarTypes.build_dict(inst), 'values':create_unknown_value()})
        elif opname[inst[1]] == 'BUILD_SLICE':
            self.vars.append({"types":VarTypes.build_slice(reordered), 'values':create_unknown_value()})
        elif opname[inst[1]] == 'BUILD_CLASS':
            self.vars.append({"types":VarTypes.build_class(reordered), 'values':create_unknown_value()})


    insts_handler.add_set(InstSet(['POP_TOP'], pop_top))
    insts_handler.add_set(InstSet(['ROT_TWO'], rot_2))
    insts_handler.add_set(InstSet(['ROT_THREE'], rot_3))
    insts_handler.add_set(InstSet(['ROT_FOUR'], rot_4))
    insts_handler.add_set(InstSet(['DUP_TOP'], dup_top))
    insts_handler.add_set(InstSet(['DUP_TOPX'], dup_topx))
#    insts_handler.add_set(InstSet(['POP_BLOCK'], pop_block))
    insts_handler.add_set(InstSet(['SETUP_LOOP'], setup_loop))
    insts_handler.add_set(InstSet(['SETUP_EXCEPT'], setup_except))
    insts_handler.add_set(InstSet(['SETUP_FINALLY'], setup_finally))
    insts_handler.add_set(InstSet(['BREAK_LOOP'], break_loop))
    insts_handler.add_set(InstSet(['BUILD_LIST', 'BUILD_TUPLE',
         'BUILD_MAP', 'BUILD_SLICE', 'BUILD_CLASS'], build_insts))


class InterprState(BaseInfoStorage):
    def __init__(self, **kwargs):
        BaseInfoStorage.__init__(self)

        # creating from __deepcopy__
        if not len(kwargs):
            return

        self._aso = {}

        if kwargs['init_stack']:
            self.stack = Stacks()
            self.stack_inited = True
        else:
            self.stack = None
            self.stack_inited = False
        del kwargs['init_stack']

        if 'shared_symtable' not in kwargs:
            newkw = copy(kwargs)
            newkw['_aso'] = self._aso
            self.smtbl = SymbolTable(**newkw)
        else:
            self.smtbl = kwargs['shared_symtable']
        self.inited = True
        self.bb_processed=False

    def _cleanup_aso(self):
        if not self.inited:
            self._aso.clear()
            return
        vids = self.stack.get_ids() | self.smtbl.get_ids()
#        print "CLEANUP_VIDS: %r" % vids
        for i in copy(self._aso.keys()):
            if i not in vids:
                del self._aso[i]

    def _update_aso(self):
        if not self.inited:
            return
        smtbl_obj = self.smtbl.get_id_vars()
        stack_obj = self.stack.get_id_vars()
        self._aso.update(smtbl_obj)
        self._aso.update(stack_obj)
        self._cleanup_aso()

    def _add_to_aso(self, obj):
        self._aso[id(obj)] = obj

    def handle_inst(self, inst_name, *args, **kwargs):
        raise Exception("%s.handle_inst shouldn't be called" % self.clsname)

    def __deepcopy__(self, memo):
        res = self.__class__()
        res.init_from(self)
        return res

    def init_from(self, other):
        other._cleanup_aso()
        if other.inited:
            _aso_trans = deepcopy(other._aso)
            _aso = {}
            for v in _aso_trans.values():
                _aso[id(v)] = v
            self._aso = _aso

#            print "0: %r\n1: %r\n2: %r\n3: %r" % (id(other.smtbl), other._aso, other.smtbl._aso,
#                    other.smtbl.locals)
            setglobal('_deep_aso_trans', _aso_trans)
            setglobal('_deep_aso', _aso)
            setglobal('_deep_fix_stack', False)
            self.smtbl = deepcopy(other.smtbl)
            self.init_stack_from(other, False)
            delglobal('_deep_aso')
            delglobal('_deep_aso_trans')
            delglobal('_deep_fix_stack')

            self.inited = True
            self.bb_processed=False
        else:
            # FIXME
            raise Exception("This shouldn't ever happen: init_from() with not inited 'other'!")
            self.inited = False


    def __create_stack_aso_trans(self, other):
        _aso_trans = {}
        o_st_ids = other.stack.get_ids()
        o_names = other.smtbl.get_id_names()
        shared_v_names = {}
        for i, name in o_names.items():
            if i in o_st_ids:
                shared_v_names[i] = name
        s_shared_vars = self.smtbl.get_items_by_names(shared_v_names.values())

#        print "o_names:", o_names
#        print "s_shared_vars:", s_shared_vars
#        print "shared_v_names:", shared_v_names
        for i, name in shared_v_names.items():
            _aso_trans[i] = s_shared_vars[name]
        return _aso_trans

    def init_stack_from(self, other, should_fix_stack=True):
        if other.stack_inited:
            if should_fix_stack:
                _aso_trans = self.__create_stack_aso_trans(other)
                setglobal('_deep_aso', self._aso)
                setglobal('_deep_aso_trans', _aso_trans)
                setglobal('_deep_fix_stack', True)
                self.stack = deepcopy(other.stack)
                delglobal('_deep_fix_stack')
                delglobal('_deep_aso_trans')
                delglobal('_deep_aso')
            else:
                self.stack = deepcopy(other.stack)
            self.stack_inited = True
        else:
            # FIXME
#            raise "HOHOHO: init_stack_from %r!" % other
            if not hasattr(self, 'stack'):
                self.stack = None
            self.stack_inited = False

    def __or__(self, other):
        res = deepcopy(self)
        res.__ior__(other)
        return res

    def __ior__(self, other):
        if self.inited:
            if self.stack_inited:
                if other.stack_inited:
                    self.stack |= other.stack
            else:
                if other.stack_inited:
                    self.stack = deepcopy(other.stack)
                    self.stack_inited = True

            self.smtbl |= other.smtbl
            self.inited = True
            other.bb_processed=True
        else:
            self.init_from(other)
        return self

    def __ne__(self, other):
        return not self == other

    def __eq__(self, other):
        return self.stack == other.stack and \
               self.smtbl == other.smtbl

    def _lge_inner(self, other):
        if self.inited:
            if other.inited:
                if self.stack_inited:
                    if other.stack_inited:
                        return map(lambda x,y: x and y,
                                   self.stack.lge(other.stack),
                                   self.smtbl.lge(other.smtbl))
                    else:
                        return (False, True, False)
                else:
                    if other.stack_inited:
                        return (True, False, False)
                    else:
                        return (False, False, True)
            else:
                return (False, True, False)
        else:
            if other.inited:
                return (True, False, False)
            else:
                return (False, False, True)

    def _repr_inner(self):
        if self.inited:
            return "Inited=%r,\t%r\n%r"% (self.inited, self.smtbl,
                                          self.stack)
        else:
            return "Not initialized"
    _pretty_inner = _repr_inner
    _show_dublicates = _pretty_inner

    def get_varvalues(self, varname):
        if varname in self.smtbl.local_names:
#            self.smtbl.locals[varname]['aliases'] =  self.smtbl.alias_store.getVarAliases(varname)
            res =  self.smtbl.locals[varname]
        elif varname in self.smtbl.global_names:
#            self.smtbl.globals[varname]['aliases'] = self.smtbl.alias_store.getVarAliases(varname)
            res = self.smtbl.globals[varname]
        else:
            return None
        return res["values"]

    def get_vartypes(self, varname):
        aliasanalysis = getglobal('aliasanalysis')
        if aliasanalysis:
            return self.smtbl.alias_store.getVarAliases(varname)

        if varname in self.smtbl.local_names:
#            self.smtbl.locals[varname]['aliases'] =  self.smtbl.alias_store.getVarAliases(varname)
            res =  self.smtbl.locals[varname]
        elif varname in self.smtbl.global_names:
#            self.smtbl.globals[varname]['aliases'] = self.smtbl.alias_store.getVarAliases(varname)
            res = self.smtbl.globals[varname]
        else:
            return None

        return res["types"]

    def get_vars(self):
        result = {'locals': {},
                  'globals': {}}
        if not self.inited:
            return result
        for varname in self.smtbl.local_names:
            self.smtbl.locals[varname]['aliases'] = self.smtbl.alias_store.getVarAliases(varname)
            result['locals'][varname] = self.smtbl.locals[varname]
        for varname in self.smtbl.global_names:
            result['globals'][varname] = self.smtbl.globals[varname]
            self.smtbl.globals[varname]['aliases'] = self.smtbl.alias_store.getVarAliases(varname)
        return result


class InterpreterStates(BaseInfoStorage):
    insts_handler = deepcopy(BaseInfoStorage.insts_handler)
    implemented_insts = set()
    implemented_insts.update(SymbolTable.implemented_insts)
    implemented_insts.update(Stacks.implemented_insts)
    implemented_insts.update(VarTypes.implemented_insts)

    def __init__(self, **kwargs):
        BaseInfoStorage.__init__(self)
        # creation not from __deepcopy__
        if len(kwargs):
            self.states = {'normal': InterprState(**kwargs)}
        else:
            self.states = {}


    def __deepcopy__(self, memo):
        res = self.__class__()
        res.init_from(self)
        return res

    def init_from(self, other):
        self.states = deepcopy(other.states)

    def init_stack_from(self, other):
        for name, v in self.states.items():
            if name in other.states and other.states[name].stack_inited:
                v.init_stack_from(other.states[name])

    def is_stacks_inited_as_parent(self, parent):
        for name, v in self.states.items():
            if name in parent.states and \
               parent.states[name].stack_inited and not v.stack_inited:
                return False
        else:
            return True

    def __getitem__(self, key):
        if key not in ('normal', 'raised'):
            raise Exception('Unknown key for %s: %r' %(self.clsname, key))
        return self.states.get(key)

    def __or__(self, other):
        res = deepcopy(other)
        res.__ior__(other)
        return res

    def __ior__(self, other):
        for key in ('normal', 'raised'):
            if key in self.states:
                if key in other.states:
                    self.states[key] |= other.states[key]
            else:
                if key in other.states:
                    self.states[key] = deepcopy(other.states[key])
        return self

    def __ne__(self, other):
        return not self == other

    def __eq__(self, other):
        return self.states.keys() == other.states.keys() and \
                all(map(lambda key: self.states[key] == other.states[key],
                                    self.states.keys()))

    def _lge_inner(self, other):
        sk = set(self.states.keys())
        ok = set(other.states.keys())

        if 'normal' in sk and 'normal' in ok:
            n_lge = self.states['normal'].lge(other.states['normal'])
        else:
            n_lge = (True, True, True)
        if 'raised' in sk and 'raised' in ok:
            r_lge = self.states['raised'].lge(other.states['raised'])
        else:
            r_lge = (True, True, True)
        less = sk <= ok and ok and r_lge[0] and n_lge[0]
        greater = sk >= ok and sk and r_lge[1] and n_lge[1]
        equal = sk == ok and r_lge[2] and n_lge[2]
        #less = sk < ok or (sk and sk == ok and r_lge[0] and n_lge[0])
        #greater = sk > ok or (sk and sk == ok and r_lge[1] and n_lge[1])
        #equal = sk == ok and r_lge[2] and n_lge[2]
        return (less, greater, equal)


    def handle_inst(self, inst_name, *args, **kwargs):
        raise Exception("%s.handle_inst shouldn't be called" % self.clsname)

    def _repr_inner(self):
        return "%s{\n%s\n}"% (self.clsname,
                  '\n'.join(map(lambda k:"%r: %r" % (k,self.states[k]),
                                self.states)))
    _pretty_inner = _repr_inner
    _show_dublicates = _pretty_inner

    def is_raised(self):
        return 'raised' in self.states

    def disable_exception(self):
        if len(self.states) == 2:
            print "WARNING: disabling exception with normal and raised states"
            self.states['normal'] |= self.states['raised']
            del self.states['raised']
        elif 'raised' in self.states:
            self.states['normal'] = self.states['raised']
            del self.states['raised']
        else:
            print "WARNING: disabling exception with no raised state"

    def raise_exception(self, push_to_stack=None):
        if push_to_stack is None:
            push_to_stack = ({"types":create_unknown(), 'values':create_unknown_value()},
                             {"types":create_unknown(), 'values':create_unknown_value()},
                             {"types":create_unknown(), 'values':create_unknown_value()})
        else:
            push_to_stack = list(push_to_stack)
            while len(push_to_stack) < 3:
                push_to_stack.insert(0, {"types":create_unknown(), 'values':create_unknown_value()})
        if len(self.states) == 2:
            print "WARNING: raising exception with normal and raised states"
            self.states['raised'] |= self.states['normal']
            self.states['raised'].stack.extend_vars(push_to_stack)
            del self.states['normal']
        else:
            self.states.values()[0].stack.extend_vars(push_to_stack)
            if 'normal' in self.states:
                self.states['raised'] = self.states['normal']
                del self.states['normal']

    def get_vartypes(self, varname):
        return dict(((stname, state.get_vartypes(varname))
                   for stname, state in self.states.items()))

    def get_varvalues(self, varname):
        return dict(((stname, state.get_varvalues(varname))
                   for stname, state in self.states.items()))

    def get_vars(self):
        return dict(((stname, state.get_vars())
                   for stname, state in self.states.items()))

setglobal('InterpreterStates', InterpreterStates)


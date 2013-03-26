# -*- coding: utf-8 -*-

from random import randint
from copy import copy, deepcopy
from itertools import *
from pytypes_run.var_operations import *

class InstSet(object):
    def __init__(self, insts, handler, def_kwargs = None):
        self.insts = set(insts)
        self.handler = handler
        if self.handler:
            self.varnames = self.handler.func_code.co_varnames
        else:
            self.varnames = ()
        if def_kwargs is not None:
            self.def_kwargs = def_kwargs
        else:
            self.def_kwargs = {}

    def __contains__(self, item):
        return item in self.insts

    def __isub__(self, other):
        self.insts -= other.insts
        return self

    def handle(self, *args, **kwargs):
        kwargs.update(self.def_kwargs)
        self_obj = kwargs['self_obj']
        for kwkey in kwargs.keys():
            if kwkey not in self.varnames:
                del kwargs[kwkey]
        return self.handler(self_obj, *args, **kwargs)

    def add_inst(self, inst_name):
        self.insts.add(inst_name)

    def __repr__(self):
        return '%s([%s]: %s(%s))' % (self.__class__.__name__,
                                  ', '.join(map(repr, self.insts)),
                                  self.handler.func_name,
                                  ', '.join(self.handler.func_code.
                                            co_varnames))

class InstsHandler(object):
    def __init__(self):
        self.sets = {}
        self.stored_insts = set()

    def __deepcopy__(self, memo):
        res = self.__class__()
        res.sets = deepcopy(self.sets)
        res.stored_insts = deepcopy(self.stored_insts)
        return res

    def _remove_from_previous(self, insts_set):
        for curset in self.sets.values():
#            union = curset.insts & insts_set.insts
#            if union:
#                print "Redefining %r" % union
            curset -= insts_set
    
    def add_set(self, insts_set, setid=None):
        if setid is None:
            if self.sets:
                setid = max(self.sets.keys()) + 1
            else:
                setid = 0
        # we may redefine some instuction handlers
        self._remove_from_previous(insts_set)

        self.sets[setid] = insts_set
        self.stored_insts.update(insts_set.insts)
        return setid

    def update(self, other):
        for insts_set in other.sets.values():
            self.add_set(insts_set)

    def add_inst_to_set(self, setid, inst_name):
        self.sets[setid].add_inst(inst_name)
        self.stored_insts.add(inst_name)


    def __contains__(self, inst_num):
        return any(inst_num in insts_set for insts_set in self.sets.values())

    def handle(self, inst_name, *args, **kwargs):
        for insts_set in self.sets.values():
            if inst_name in insts_set:
                return insts_set.handle(*args, **kwargs)
        else:
            raise NotImplementedError("Instruction %r hasn't been implemented!" % \
                                  inst_name)

    def __repr__(self):
        return '%s([%s])' % (self.__class__.__name__,
                                 ', '.join(map(repr, self.sets.values())))

class BaseInstHandler(object):
    insts_handler = InstsHandler()
    implemented_insts = insts_handler.stored_insts

    def __init__(self):
        self.rd_instances = []
        self.redirected_insts = set()
        self.clsname = self.__class__.__name__

    def clear_redirect_instances(self):
        del self.rd_instances[:]
        self.redirected_insts.clear()

    def add_redirect_instance(self, instance):
        self.rd_instances.append(instance)
        self.redirected_insts.update(instance.implemented_insts)
        self.redirected_insts.update(instance.redirected_insts)


    def handle_inst_rd(self, inst_name, *args, **kwargs):
        for rd_instance in self.rd_instances:
            if rd_instance.implement_inst(inst_name):
                kwargs['self_obj'] = rd_instance
                return rd_instance.handle_inst(inst_name, *args, **kwargs)
        else:
            raise NotImplementedError("Desync of 'redirected_insts' and 'rd_instances': %s (%r)" % \
                                      (self.__class__.__name__, inst_name))

    def __deepcopy__(self, memo):
        raise NotImplementedError("%s.__deepcopy__" % self.clsname)

    def handle_inst(self, inst_name, *args, **kwargs):
        if inst_name in self.implemented_insts:
            kwargs['self_obj'] = self
            return self.insts_handler.handle(inst_name, *args, **kwargs)
        elif inst_name in self.redirected_insts:
            return self.handle_inst_rd(inst_name, *args, **kwargs)
        else:
            raise NotImplementedError("%s doesn't implement instruction %r" % \
                     (self.__class__.__name__, inst_name))

    def implement_inst(self, inst_name):
        return (inst_name in self.implemented_insts) or \
                      (inst_name in self.redirected_insts)

    def do_nothing(self, *args, **kwargs):
        pass


class BaseInfoStorage(BaseInstHandler):
    def _repr_inner(self, *args, **kwargs):
        raise NotImplementedError("%s.repr" % self.clsname)

    def __repr__(self, *args, **kwargs):
        rc = getglobal('repr_counter')
        # checking for cyclic references
        if rc > 20:
            print "Warning: repr_counter reached %r - possibly got cyclic references" % rc
            return "..."
        elif id(self) in repr_list:
            if getglobal('dublicate_repr'):
                return self._show_dublicates()
            else:
                setglobal('dublicate_repr', True)
    #            print "Info: got cyclic references for %r" % self.clsname
                res = "Dublicate{%s}" % self._show_dublicates()
                setglobal('dublicate_repr', False)
                return res
        else:
            setglobal('repr_counter', rc + 1)
            repr_list.append(id(self))
            #            print "======== repr_counter reached %r" % lc
            if getglobal('DEBUG_PRINT'):
                rres = self._repr_inner(*args, **kwargs)
            else:
                rres = self._pretty_inner(*args, **kwargs)
            repr_list.pop()
            setglobal('repr_counter', rc)
            return rres

    def _show_dublicates(self, *args, **kwargs):
        raise NotImplementedError("%s._show_dublicates" % self.clsname)

    def _pretty_inner(self, *args, **kwargs):
        raise NotImplementedError("%s._pretty_inner" % self.clsname)

    def _lge_inner(self, *args, **kwargs):
        raise NotImplementedError("%s.lge" % self.clsname)

    def lge(self, *args, **kwargs):
        lc = getglobal('lge_counter')
        # checking for cyclic references
        if lc > 20:
            print "Warning: lge_counter reached %r - possibly got cyclic references" % lc
            return (0, 0, 1)
        else:
            setglobal('lge_counter', lc + 1)
#            print "======== lge_counter reached %r" % lc
            lres = self._lge_inner(*args, **kwargs)
            setglobal('lge_counter', lc)
            return lres


class BaseType(BaseInfoStorage):
    implemented_types = ()

    def __init__(self):
        BaseInfoStorage.__init__(self)
        #self.objid = randint(0, 4294967295L)
        self.objid = id(self)
        self.stored_types = set()

    def _repr_inner(self):
        return '%s(%s)' % (self.clsname,
                           ', '.join(map(repr, self.stored_types)))

    def _list_names(self):
        return set(self.implemented_types)

    def clear(self):
        self.stored_types.clear()

    def __ne__(self, other):
        return not self.lge(other)[2]

    def __eq__(self, other):
        return self.lge(other)[2]

    def create(self, value):
        if isinstance(value, self.__class__):
            self.create_from(value)
        else:
            self.create_from_const(value)

    def create_from(self, *args, **kwargs):
        raise NotImplementedError("%s.create_from" % self.clsname)

    def create_from_const(self, *args, **kwargs):
        raise NotImplementedError("%s.create_from_const" % self.clsname)


    def __div__(self, *args, **kwargs):
        raise NotImplementedError("%s.__div___" % self.clsname)

    def __or__(self, other):
        return deepcopy(self).__ior__(other)

    def __ior__(self, value):
        if isinstance(value, self.__class__):
            self.add_type(value)
        else:
            self.add_const(value)
        return self

    def add_type(self, other):
        raise NotImplementedError("%s.add_type" % self.clsname)

    def add_const(self, const):
        raise NotImplementedError("%s.add_const" % self.clsname)

    def implement_types(self, typesset):
        return all(imap(lambda x: x in self.implemented_types, typesset))

    def check_current_type(self):
        for typename in self.stored_types:
            if typename not in self.implemented_types:
                raise NotImplementedError("%s doesn't implement type '%s'" % \
                         (self.clsname, typename))

def setglobal(name, var):
    globals()['__builtins__'][name] = var
#__builtins__['mydebugDict'] = {} # для использования cProfiler

def getglobal(name):
    if name in globals()['__builtins__']:
        return globals()['__builtins__'][name]
    else:
        return None

def delglobal(name):
    if name in globals()['__builtins__']:
        del globals()['__builtins__'][name]

setglobal('delglobal', delglobal)

import os
def getabspath(path, prefix=None):
    if prefix is None:
        return os.path.abspath(path)
    else:
        return os.path.join(prefix, path)
setglobal('getabspath', getabspath)

def getmodulename(path):
    return os.path.splitext(os.path.basename(path))[0]
setglobal('getmodulename', getmodulename)

def getcurpath():
    cur_module = modules_stack[-1]
    res = cur_module.names[cur_module.last_name]
    if len(res) > 3 and res[-3:] == '.py':
        res = os.path.dirname(res)
    return res
setglobal('getcurpath', getcurpath)



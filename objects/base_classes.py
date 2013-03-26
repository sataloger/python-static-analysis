# -*- coding: utf-8 -*-
from copy import deepcopy
from analyzer.py_run.functions import setglobal, getglobal

class HandlerStorage(object):
    insts_handlers = {}
#    def __init__(self):
#        self.

    def handle(self, inst, *args, **kwargs):
        if inst not in self.insts_handlers.keys():
            raise NotImplementedError("Instruction %s is not implemented in class %s" % (inst, self.__class__.__name__))
        varnames = self.insts_handlers[inst].func_code.co_varnames
        for kwkey in kwargs.keys():
            if kwkey not in varnames:
                del kwargs[kwkey]
        return self.insts_handlers[inst](self, *args, **kwargs)

    def add_inst(self, inst_name,handler):
        self.insts_handlers[inst_name] = handler

    def __repr__(self):
        return "\n".join(["[ %s : %s ]" % (k, v) for k, v in self.insts_handlers.iteritems()])

class BaseInfoStorage(object):
    insts_handlers = HandlerStorage()

    def _repr_inner(self, *args, **kwargs):
        raise NotImplementedError("%s.repr" % self.__class__.__name__)

    def __repr__(self):
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
        raise NotImplementedError("%s._show_dublicates" % self.__class__.__name__)

    def _pretty_inner(self, *args, **kwargs):
        raise NotImplementedError("%s._pretty_inner" % self.__class__.__name__)

    def _lge_inner(self, *args, **kwargs):
        raise NotImplementedError("%s.lge" % self.__class__.__name__)

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



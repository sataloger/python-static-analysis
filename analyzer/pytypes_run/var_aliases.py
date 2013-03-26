# -*- coding: utf-8 -*-

import sys
import itertools
from random import randint
from copy import copy, deepcopy
from opcode import opname
from itertools import *

from pytypes_run.var_operations import *
from pytypes_run.base_classes import *


class Variable(object):
    def __init__(self,varname, varprefix):
        self.varname = varname
        self.varprefix = varprefix
        
    def __str__(self):
        return self.varprefix + "." + self.varname
    __repr__ = __str__

    def __eq__(self, other):
        return (self.varname == other.varname) and (self.varprefix == other.varprefix)

    def __hash__(self):
        return hash(self.varprefix + "." + self.varname)



class AliasStorage(BaseInfoStorage):
    def __init__(self,prefix = None):
        BaseInfoStorage.__init__(self)
        self.vars = {}
        self.baseprefix = prefix
        
    def __getitem__(self, item):
        return self.vars[item]

    def search_prefix(self, maxprefix, varname):
        prefix_list = maxprefix.split(".")

        while len(prefix_list):
            prefix_join = ".".join(prefix_list)

            try:
                return self.vars[prefix_join + "." + varname]
            except KeyError:
                pass
            prefix_list = prefix_list[:-1]
        try:
            return self.vars["global." + varname]
        except KeyError:
            pass
        from pprint import pprint
        pprint(self.vars)
        print maxprefix + "." + varname
        print maxprefix + "." + varname in self.vars
        raise KeyError("Variable " + varname + " with maxprefix " + maxprefix + " wasn't found.")
#            if cur_prrix.fin:

    def addVar(self,varname,varprefix, path):
        print "\n\n---------------------addVar------------------------------"
        print varprefix + "." + varname, path
        print "---------------------------------------------------------"

        for key, val in self.vars.items():
            if val.varprefix + "." + val.varname == varprefix + "." + varname:
                print "WARNING: variable overwrite: %r %r %r" % (varname,varprefix, path)
#                raise Exception()
            
        self.vars[varprefix + "." + varname] = VarAliases(varname, varprefix, self.baseprefix)

    def delVar(self,varname,varprefix, path):
        print "\n\n---------------------delVar------------------------------"
        print varprefix + "." + varname, path
        print "---------------------------------------------------------"

        # remove var from may connection
        for alias_val in self.vars[varprefix + "." + varname].get_may_aliases():
            if  alias_val.varprefix + "." + alias_val.varname in self.vars:
                self.vars[alias_val.varprefix + "." + alias_val.varname].del_may_alias(varprefix, varname)


        # remove var from must connection
        for alias_val in self.vars[varprefix + "." + varname].get_must_aliases():
            if  alias_val.varprefix + "." + alias_val.varname in self.vars:
                self.vars[alias_val.varprefix + "." + alias_val.varname].del_must_alias(varprefix, varname)

        # del alias entity
        self.vars[varprefix + "." + varname].clear_aliases()
#        self.vars.pop(varprefix + "." + varname)
        print self.vars
        print "---------------------------------------------------------"


    def addAlias(self, lvar , rvar, onlymay = False):
        print "---------------------addAlias----------------------------"
        print lvar
        print rvar
        print "---------------------------------------------------------"
#        print "------- 1------------"
#        from pprint import pprint
#        pprint(self.vars)
#        print "---------------------"

        # non-variable assign
        if rvar.varname is None:
            for var in self.vars[lvar.varprefix + "." + lvar.varname].get_may_aliases():
                self.vars[var.varprefix + "." + var.varname].del_alias(lvar.varname, lvar.varprefix)
            lvar.clear_aliases()
            return

        # self assign:
        if lvar == rvar:
            return

        if (rvar.varprefix + "." + rvar.varname) not in self.vars:
#            print lvar.varprefix, lvar
            print rvar.varprefix + "." + rvar.varname
            print "is not in Vars"
            for key, var in self.vars.items():
                print var.varprefix + "." + var.varname
            print "WARNING: External variables can't be propertly handled."

#            #check rvar may aliases
            for rmay in rvar.get_may_aliases():
                for k, svar in self.vars.iteritems():
                    #if rvar may alias is in self.vars
                    if svar == rmay:
                        #then append all svar may aliases to lvar
                        self.addAlias(lvar,svar,True)
                        #WARNING: probably some deeply indirected aliases will be loosed
                        pass

            if not onlymay:
    #            #check rvar must aliases
                for rmust in rvar.get_must_aliases():
                    for k, svar in self.vars.iteritems():
                        #if rvar must alias is in self.vars
                        if svar == rmust:
                            #then append all svar must aliases to lvar
                            self.addAlias(lvar,svar)
                            #WARNING: probably some deeply indirected aliases will be loosed


            # parent nesting
            if lvar.varprefix.find(rvar.varprefix) != -1:
                self.vars[lvar.varprefix + "." + lvar.varname].add_may_alias(rvar.varname,rvar.varprefix)
                if not onlymay:
                    self.vars[lvar.varprefix + "." + lvar.varname].add_must_alias(rvar.varname,rvar.varprefix)
            return
#        print self.vars[lvar.varprefix + "." + lvar.varname] == lvar
        # lvar is global - merge aliases
#        if self.vars[lvar.varprefix + "." + lvar.varname] != lvar:
#            for als in lvar.get_may_aliases():
#                if als.varprefix + "." + als.varname in self.vars:
#                    self.vars[lvar.varprefix + "." + lvar.varname].add_may_alias(als.varname, als.varprefix)
#            for als in lvar.get_must_aliases():
#                if als.varprefix + "." + als.varname in self.vars:
#                    self.vars[lvar.varprefix + "." + lvar.varname].add_must_alias(als.varname, als.varprefix)
#
#        # rvar is global - merge aliases
#        if self.vars[rvar.varprefix + "." + rvar.varname] != rvar:
#            for als in rvar.get_may_aliases():
#                if als.varprefix + "." + als.varname in self.vars:
#                    self.vars[rvar.varprefix + "." + rvar.varname].add_may_alias(als.varname, als.varprefix)
#            for als in rvar.get_must_aliases():
#                if als.varprefix + "." + als.varname in self.vars:
#                    self.vars[rvar.varprefix + "." + rvar.varname].add_must_alias(als.varname, als.varprefix)

        # indirect aliases
        for var in self.vars[rvar.varprefix + "." + rvar.varname].get_may_aliases():
            try:
                self.vars[lvar.varprefix + "." + lvar.varname].add_may_alias(var.varname,var.varprefix)
                self.vars[var.varprefix + "." + var.varname].add_may_alias(lvar.varname,lvar.varprefix)
            except KeyError:
                pass
        if not onlymay:
            for var in self.vars[rvar.varprefix + "." + rvar.varname].get_must_aliases():
                try:
                    self.vars[lvar.varprefix + "." + lvar.varname].add_must_alias(var.varname,var.varprefix)
                    self.vars[var.varprefix + "." + var.varname].add_must_alias(lvar.varname,lvar.varprefix)
                except KeyError:
                    pass

        for var in self.vars[lvar.varprefix + "." + lvar.varname].get_may_aliases():
            try:
                self.vars[rvar.varprefix + "." + rvar.varname].add_may_alias(var.varname,var.varprefix)
                self.vars[var.varprefix + "." + var.varname].add_may_alias(rvar.varname,rvar.varprefix)
            except KeyError:
                pass

        if not onlymay:
            for var in self.vars[lvar.varprefix + "." + lvar.varname].get_must_aliases():
                try:
                    self.vars[rvar.varprefix + "." + rvar.varname].add_must_alias(var.varname,var.varprefix)
                    self.vars[var.varprefix + "." + var.varname].add_must_alias(rvar.varname,rvar.varprefix)
                except KeyError:
                    pass

        # direct aliases
        self.vars[lvar.varprefix + "." + lvar.varname].add_may_alias(rvar.varname,rvar.varprefix)
        if not onlymay:
            self.vars[lvar.varprefix + "." + lvar.varname].add_must_alias(rvar.varname,rvar.varprefix)
        
        self.vars[rvar.varprefix + "." + rvar.varname].add_may_alias(lvar.varname,lvar.varprefix)
        if not onlymay:
            self.vars[rvar.varprefix + "." + rvar.varname].add_must_alias(lvar.varname,lvar.varprefix)

#        print "------- 2------------"
#        from pprint import pprint
#        pprint(self.vars)
#        print "---------------------"

    def getVarAliases(self,varname,baseprefix = None):
        if baseprefix is None:
            baseprefix = self.baseprefix

        for var in  self.vars.values():
            if var.varname == varname:
                return var
        else:
            print "Variable %r not found in " % varname
            print [var for var in self.vars]
#            raise Exception()
            return None

    def __repr__(self):
        res = ""
        for key, var in self.vars.items():
            res+= "\n\t\t %r" % var
        return res
    __str__ = __repr__

    def __ior__(self,other):
        ck = set(self.vars.keys())
        pk = set(other.vars.keys())


        for key in pk:
            if key not in ck:
                # parent has new key
                self.addVar(other.vars[key].varname, other.vars[key].varprefix, other.vars[key].path, other.vars[key],True)

        for var in ck:
            self.vars[var] |= other.vars[var]
        return self

    def __deepcopy__(self, memo):
        res = self.__class__()
        res.vars = deepcopy(self.vars)
        return res

    
    def _lge_inner(self,other):
        lge_list = [self.vars[var].lge(other.vars[var])
                      for var in self.vars]
        if lge_list:
            if len(lge_list) > 1:
                return map(all, map(None, *lge_list))
            else:
                return lge_list[0]
        else:
            return (0,0,1)
    
class VarAliases(BaseInfoStorage):
    insts_handler = deepcopy(BaseInfoStorage.insts_handler)
    implemented_insts = insts_handler.stored_insts

    def __init__(self, varname, varprefix, baseprefix, init_aliases=None, onlymay = False):

        BaseInfoStorage.__init__(self)
        self.varname = varname
        self.varprefix  = varprefix
        self.baseprefix = baseprefix
        self.may_aliases  = set()
        self.must_aliases = set()

        if isinstance(init_aliases, VarAliases):
            self.may_aliases=init_aliases.may_aliases
            if not onlymay:
                self.must_aliases=init_aliases.must_aliases
        elif init_aliases is not None:
            for (varname,prefix) in init_aliases:
                self.add_may_alias((varname,prefix))
                if not onlymay:
                    self.add_must_alias((varname,prefix))

    def _repr_inner(self, *args, **kwargs):
#        if self.varprefix == self.baseprefix:
#            res = "%s : " % self.varname
#        else:
#            res = "%s.%s : " % (self.varprefix, self.varname)
        res = "%s.%s : " % (self.varprefix, self.varname)

        res += 'VarAliases{ MAY ('
        if len(self.may_aliases):
            lst = []
            for val in self.may_aliases:
                if val.varprefix == self.baseprefix and 1==0:
                    lst.append("%s" % val.varname)
                else:
                    lst.append("%s.%s" % (val.varprefix, val.varname))
            res += ', '.join(lst)
        else:
            res += 'none'
        res += ') MUST ('
        if len(self.must_aliases):
            lst = []
            for val in self.must_aliases:
                if val.varprefix == self.baseprefix and 1==0:
                    lst.append("%s" % val.varname)
                else:
                    lst.append("%s.%s" % (val.varprefix, val.varname))
            res += ', '.join(lst)
        else:
            res += 'none'
        res += ')}'
        return res
    
    _pretty_inner = _repr_inner

    def __deepcopy__(self, memo):
        res = self.__class__( self.varname, self.varprefix, self.baseprefix )
        res.may_aliases = deepcopy(self.may_aliases)
        res.must_aliases = deepcopy(self.must_aliases)
        return res


    def add_may_alias(self, varname, prefix):
        if self.varname == varname and self.varprefix ==prefix:
            return False
        for var in self.may_aliases:
            if var.varname == varname and var.varprefix ==prefix:
                return False

        if Variable(varname,prefix) not in self.may_aliases:
            self.may_aliases.add( Variable(varname,prefix))
            return True
        else:
            print "Warning: duplicate may alias (%s,%s)" % varname
            return False


    def add_must_alias(self, varname, prefix):
        if self.varname == varname and self.varprefix ==prefix:
            return False
        for var in self.must_aliases:
            if var.varname == varname and var.varprefix ==prefix:
                return False
        if Variable(varname,prefix) not in self.must_aliases:
            self.must_aliases.add( Variable(varname,prefix) )
            return True
        else:
            print "Warning: duplicate must alias (%s, %s)" % varname
            return False

    def add_alias(self, varname, prefix):
        var = Variable(varname,prefix)
        if (var not in self.must_aliases) & (var not in self.may_aliases):
            self.must_aliases.add(var)
            self.may_aliases.add(var)
        else:
            print "Warning: duplicate alias (%s, %s)" % (varname,prefix)
        
    def get_may_aliases(self):
        return self.may_aliases
        
    def get_must_aliases(self):
        return self.must_aliases
        

    def del_may_alias(self, prefix, varname):
        try:
            var = Variable(varname,prefix)
            self.may_aliases.remove(var)
        except KeyError:
            print "Warning: delete non-existed may alias " +str(var) + " from " + self.varprefix + "." + self.varname
        
    def del_must_alias(self, prefix, varname):
        try:
            var = Variable(varname,prefix)
            self.must_aliases.remove(var)
        except KeyError:
            print "Warning: delete non-existed must alias " + str(var) + " from " + self.varprefix + "." + self.varname


#    def del_alias(self, varname, prefix):
#        print self.may_aliases
#        try:
#            var = Variable(varname,prefix)
#            print var
#            print var in self.may_aliases
#            print var in self.must_aliases
#
#            self.may_aliases.remove(var)
#            self.must_aliases.remove(var)
#        except KeyError:
#            print "Warning: delete non-existed alias \'" + str(var) + "\' from " + self.varprefix + "." + self.varname


    """
    def clear_may_aliases(self):
        self.may_aliases.clear()                    
                
    def clear_must_aliases(self):
        self.must_aliases.clear()
    """

    def clear_aliases(self):
        self.may_aliases.clear()
        self.must_aliases.clear()

    def __nonzero__(self):
        #must aliases includes
        return len(self.may_aliases)

    def __eq__(self, other):
        res = (self.varname == other.varname) and (self.varprefix == other.varprefix)
        if isinstance(self, VarAliases) and isinstance(other, VarAliases):
            res = res and (self.may_aliases == other.may_aliases) and (self.must_aliases == other.must_aliases)
        return res

    def __ior__(self, other):
        self.may_aliases.update(other.may_aliases)
        self.must_aliases.intersection_update(other.must_aliases)
        return self

    def __or__(self, other):
        res = self.__class__()
        res.__ior__(other)
        return res

    def _lge_inner(self, other):
        less = (self.may_aliases < other.may_aliases) and (self.must_aliases < other.must_aliases)
        greater = (self.may_aliases > other.may_aliases) and (self.must_aliases > other.must_aliases)
        equal = (self.may_aliases == other.may_aliases) and (self.must_aliases == other.must_aliases)
        return (less, greater, equal)
    
#
#    def __deepcopy__(self, memo):
#        res = self.__class__(self.varname,self.varprefix)
#        res.may_aliases= deepcopy(self.may_aliases)
#        res.must_aliases= deepcopy(self.must_aliases)
#        return res

def create_empty_alias(name,prefix,aliases=None):
    return VarAliases(name, prefix, baseprefix = None, init_aliases = aliases)

setglobal('AliasStorage',AliasStorage)
setglobal('VarAliases', VarAliases)
setglobal('create_empty_alias', create_empty_alias)



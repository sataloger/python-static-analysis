#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
import symtable
import os
import sys
from optparse import OptionParser

def describe_symbol(sym, prefix=''):
    assert isinstance(sym, symtable.Symbol)
    print "%s%-20s" % (prefix, sym.get_name()),

    for prop in dir(sym):
        if prop.startswith('is_') and (prop not in ('is_keywordarg', 'is_vararg', 'is_in_tuple')):
            if getattr(sym, prop)():
                print '%s' % prop[3:],
    print

def describe_symtable(st, recursive=True, indent=0):
    def print_d(s, *args):
        prefix = ' ' * indent
        print prefix + s, ' '.join(map(str, args))

    assert isinstance(st, symtable.SymbolTable)
    tp = st.get_type()
    print_d('Symtable: type=%s, id=%s, name=%s' % (tp, st.get_id(), st.get_name()))
#    print_d('  nested:', st.is_nested())
    print_d('  has children:', st.has_children())
#    print_d('  identifiers:', list(st.get_identifiers()))
    if tp == 'function':
        print_d('  globals:', list(st.get_globals()))
        print_d('  locals:', list(st.get_locals()))
        print_d('  frees:', list(st.get_frees()))
        print_d('  params:', list(st.get_parameters()))
    elif tp == 'class':
        print_d('  methods:', list(st.get_methods()))
    else:
        print_d('  identifiers:', list(st.get_identifiers()))

    print_d('  symbols:')
    for child_id in st.get_symbols():
        if child_id not in st.get_children():
            describe_symbol(child_id, ' ' * (indent + 4))

    if recursive:
        for child_st in st.get_children():
            describe_symtable(child_st, recursive, indent + 2)


if __name__ == '__main__':
    parser = OptionParser()
    parser.set_usage("%s filename" % (sys.argv[0]))
    options, args = parser.parse_args()
    
    if len(args) != 1:
        parser.print_usage()
        print "Try `%s -h` for more information." % sys.argv[0]
        sys.exit(0)

    if os.path.exists(args[0]):
        self_sm = symtable.symtable(open(args[0]).read(), args[0], 'exec')
        describe_symtable(self_sm)
    else:
        print "Error: file doesn't exist."



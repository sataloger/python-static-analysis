# -*- coding: utf-8 -*-

from __future__ import with_statement
import sys
import os
import re
import itertools
from random import randint
from copy import copy, deepcopy
from collections import deque
from itertools import *
from opcode import opname

from pytypes_run.var_operations import *
from pytypes_run.base_classes import *
from pytypes_run.type_callable import TypeModule
from pytypes_run.interpr_state import SymbolTable

from pytypes_run.ast_adds import get_line_nums
from analyzer.pytypes_run.base_classes import setglobal
import cfg_wrapper

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.styles import get_style_by_name
from pygments.token import Token
from pygments.formatters.html import escape_html
from pprint import pformat
from pprint import pprint

myvar = "background-color: #C3D9FF; border-color: #20C; border-style: dotted; border-width: 1px;"
myconst = ""
#myconst = "background-color: #59BFB3; border-color: #1B887A; border-style: solid; border-width: 1px;"

class ProcessModule(object):
#    def __init__(self):
#        self.curPath = os.path.dirname(getattr(sys.modules[__name__], '__file__'))

    #должна подгружать описания стандартных классов, функций
#    def load_annotation(self, fileName):
#        confReader = common.ConfigReader()
#        confReader.load_conf(fileName)
#        self.annotation = confReader.get_conf()

    def process(self, fname):
        setglobal('lge_counter', 0)
        setglobal('repr_counter', 0)
        setglobal('call_counter', 0)
        setglobal('repr_list', [])
        setglobal('lge_list', [])
#        self.__module = cfg_wrapper.MyModule(base_instance = deepcopy(module))
        try:
            RootState
        except NameError:
            SymbolTable.create_root_symtable()
            TypeModule._set_state(RootState)

        top_module = TypeModule.from_code(fname)
        self.__module = top_module.module
#        print module_symtables


    @staticmethod
    def findlinestarts(code):
        """Find the offsets in a byte code which are start of lines in the source.

        Generate pairs (offset, lineno) as described in Python/compile.c.

        """
        byte_increments = [ord(c) for c in code.co_lnotab[0::2]]
        line_increments = [ord(c) for c in code.co_lnotab[1::2]]

        lastlineno = None
        lineno = code.co_firstlineno
        addr = 0
        for byte_incr, line_incr in zip(byte_increments, line_increments):
            if byte_incr:
                if lineno != lastlineno:
                    yield (addr, lineno)
                    lastlineno = lineno
                addr += byte_incr
            lineno += line_incr
        if lineno != lastlineno:
            yield (addr, lineno)

    @staticmethod
    def findlineends(cfg):
        """Find the offsets in a byte code which are start of lines in the source.

        Generate pairs (offset, lineno) as described in Python/compile.c.

        """
        linestarts = dict(ProcessModule.findlinestarts(cfg.codeobj))
        #linestarts = dict(map(lambda x,y:(y,x),
                              #ProcessModule.findlinestarts(cfg.codeobj)))
        previnst = None
        prevline = None
        for instno in sorted(cfg.all_insts):
            if instno in linestarts:
                if prevline is not None:
                    yield previnst, prevline
                prevline = linestarts[instno]
            previnst = instno
        yield previnst, prevline

    def find_changed_places(self, attrName):
        self.changedLinesList = []
        for codeObj in self.__cfg:
            if 'states' in codeObj['bbs'][len(codeObj['bbs'])-1]:
                # проверка для того, чтобы не пытаться тут
                # обрабатывать те codeObj, на которых упали ранее
                lineStarts = [curSt for curSt in self.findlinestarts(codeObj['self_code'])]
                changedTypePlaces = getattr(codeObj['bbs'][len(codeObj['bbs'])-1]['state'], attrName)
                for instrNum in changedTypePlaces.keys():
                    oldInstrNum = 0
                    countPos = 0
                    for curInstrNum, curLineNum in lineStarts:
                        if oldInstrNum <= instrNum < curInstrNum:
#                            lineNum = curLineNum
                            break
                        oldInstrNum = curInstrNum
                        countPos += 1
                    else:
                        countPos = len(lineStarts)
                    lineNum = lineStarts[countPos-1][1]
                    self.changedLinesList.append((lineNum, changedTypePlaces[instrNum]))

        #объединяем информацию в одних по номерам строках
        self.changedLines = {}
        for lineNum, changedTypeInfo in self.changedLinesList:
            if lineNum not in self.changedLines:
                self.changedLines[lineNum] = {}
            for curVar in changedTypeInfo.keys():
                if curVar not in self.changedLines[lineNum]:
                    self.changedLines[lineNum][curVar] = changedTypeInfo[curVar]
                else:
                    self.changedLines[lineNum][curVar] |= changedTypeInfo[curVar]


    def save_to_file(self, oldfname, newfname, infotype='html'):
        getattr(self, '_save_to_file_%s' % infotype)(oldfname, newfname)

    def _save_to_file_comments(self, oldfname, newfname):
        print "Adding comments not implemented yet."

    def _save_to_file_asserts(self, oldfname, newfname):
        print "Adding assert not implemented yet."

    def _save_to_file_stats(self, oldfname, newfname):
        import cPickle
        fname = 'all_pytypes.pickled'
        _megastore.prepickle()
        with open(fname, 'w') as fout:
            cPickle.dump(_megastore, fout, cPickle.HIGHEST_PROTOCOL)

    def _save_to_file_stats_old(self, oldfname, newfname):
        self._pickle_results_all('all_pytypes.pickled')

    def _pickle_results_all(self, fname):
        import cPickle
        import binascii
        if os.path.exists(fname):
            try:
                with open(fname) as fin:
                    vtypes = cPickle.load(fin)
            except EOFError:
                vtypes = {}
        else:
            vtypes = {}

        for cfgname, cfg in self.__module.cfg.items():
            fullname = os.path.dirname(cfg.codeobj.co_filename)
            pos = fullname.find('/genshi/')
            if pos == -1:
                fullname = cfgname
            else:
                l = len('/genshi/')
                fullname = fullname[pos+l:]
                fullname = "%s.%s" % (fullname.replace('/', '.'), cfgname)
            curtypes = {}
            for bbid, bb in cfg.bbs.items():
                bbtypes = {}
                for st in bb.states.states.values():
                    vars = st.get_vars()
                    for vname, v in vars['locals'].items():
                        if vname not in bbtypes:
                            bbtypes[vname] = set()
                        bbtypes[vname].update(v._list_names())
                curtypes[bbid] = {'borders': (bb.insts_list[0][0],
                                              bb.insts_list[-1][0]),
                                  'types': bbtypes,
                                 }
            curtypes['__code_str'] = binascii.hexlify(cfg.code)
            vtypes[fullname] = curtypes

        with open(fname, 'w') as fout:
            cPickle.dump(vtypes, fout, cPickle.HIGHEST_PROTOCOL)


    def _save_to_file_stdout(self, oldfname, newfname):
        vtypes = {}
        for cfgname, cfg in self.__module.cfg.items():
            fullname = os.path.dirname(cfg.codeobj.co_filename)
            pos = fullname.find('/genshi/')
            if pos == -1:
                fullname = cfgname
            else:
                l = len('/genshi/')
                fullname = fullname[pos+l:]
                fullname = "%s.%s" % (fullname.replace('/', '.'), cfgname)
            print "Fullname = %r" % fullname
            curtypes = {}
            for bbid, bb in cfg.bbs.items():
                bbtypes = {}
                for st in bb.states.states.values():
                    vars = st.get_vars()
                    for vname, v in vars['locals'].items():
                        if vname not in bbtypes:
                            bbtypes[vname] = set()
                        bbtypes[vname].update(v['types']._list_names())
                curtypes[bbid] = bbtypes
            if 'exit' in curtypes:
                curtypes = curtypes['exit']
            else:
                if 'entry' in curtypes:
                    del curtypes['entry']
                if curtypes:
                    curtypes = curtypes[max(curtypes)]
            vtypes[fullname] = curtypes

        print " ---res---"
        from pprint import pprint
        pprint(vtypes)


    def _save_to_file_check_trace(self, fname, trace_info):
        print
        print "-----------------------------"
        print "Comparing results starts here"
        print fname
        print trace_info.keys()

    def _save_to_file_html(self, oldfname, newfname):
        import encodings
        lexer = get_lexer_by_name("python", stripall=True)
        #formatter = HtmlFormatter(linenos=True, cssclass="source",
                                 #style=get_style_by_name('colorful'))
        formatter = MyHtmlFormatter(linenos='inline',module=self.__module)
        print "MODULE", self.__module
        encodings.search_function('utf8')
        ##next command for win

        source = encodings.utf_8.decode(open(oldfname, 'r').read())[0]
        result = highlight(source, lexer, formatter)
        outfile = open(newfname, 'w')
        outfile.write('''
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN"
  "http://www.w3.org/TR/html4/strict.dtd">

<html>
<head>
  <title></title>
  <meta http-equiv="content-type" content="text/html; charset=utf-8">
  <style type="text/css">\n''')
        outfile.write(formatter.get_style_defs() + '\n')
        outfile.write('.highlight { line-height: 1.2em }\n')
        outfile.write('''
  </style>
</head>
<body>
<h2></h2>\n''')
        outfile.write(encodings.utf_8.encode(result)[0])
        outfile.close()

class BaseModuleInfo(object):
    def __init__(self, module):
        self.module = module
        self.getlinestate()

    def getlinestate(self):
        linestates = {}
        for cfg in self.module.cfg.values():
            for instno, lineno in ProcessModule.findlineends(cfg):
                got_lineno = False
                while not got_lineno:
                    for bbid, bb in cfg.bbs.items():
                        if instno in bb.insts:
                            linestates[lineno] = (cfg.prefix, bbid,
                                getattr(bb, 'transformed_states',None))
                            got_lineno = True
                            break
                    instno -= 1
        self.linestates = linestates

    @staticmethod
    def get_vartypes(name_state, varname):
        if name_state is None:
            return "Strange error"
        name, bbid, states = name_state
        if states is not None:
            return pformat(states.get_vartypes(varname))
        else:
            return "Unreachable code line in '%s'" % varname

    @staticmethod
    def get_varvalues(name_state, varname):
        if name_state is None:
            return "Strange error"
        name, bbid, states = name_state
        if states is not None:
            return pformat(states.get_varvalues(varname))
        else:
            return "Unknown"


class ModuleModifier(BaseModuleInfo):
    def __init__(self, module, text):
        BaseModuleInfo.__init__(self, module)
        self.text = text
        self.line_nums = list(map(lambda x: x-1,
                          get_line_nums('\n'.join(text))))
        _def_line = lambda line: re.search('elif|else|except|finally', line)

        for i, l in enumerate(self.text):
            if _def_line(l):
                self.line_nums.append(i)
        self.line_nums = sorted(set(self.line_nums))
        xx = {}
        for i in range(len(self.line_nums)-1):
            for j in range(self.line_nums[i], self.line_nums[i+1]):
                xx[j] = {'u': self.line_nums[i],
                         'd': self.line_nums[i+1],
                        }
        xx[self.line_nums[-1]] = {'u':self.line_nums[-1],
                                  'd':self.line_nums[-1],
                                 }
        self.line_nums2 = xx

    def _get_up_down(self, lnum):
        if lnum < self.line_nums[0]:
            return self.line_nums[0], self.line_nums[0]
        elif lnum >= self.line_nums[-1]:
            return self.line_nums[-1], self.line_nums[-1]

        return self.line_nums2[lnum]['u'], self.line_nums2[lnum]['d']

    def add_info(self):
        var_places = {}
        for lnum in self.linestates.keys():
            lnum = lnum-1
            if lnum > max(self.line_nums2.keys()):
                lnum = max(self.line_nums2.keys())
            up, down = self._get_up_down(lnum)
            obj_name, bbid, states = self.linestates.get(lnum+1, ('', -1, None))
            if states is None:
                #print 'Warning: line %i with empty states.' % lnum
                continue
            vars = states.get_vars().values()[0]
            varnames = vars['locals'].keys()# + vars['globals'].keys()
            varnames = filter(lambda v: not re.match('_\[(\d+)\]', v), varnames)
            varnames = filter(lambda v: vars['locals'][v], varnames)
            place = down
            if place not in var_places:
                var_places[place] = {'vars': set(),
                                     'prefix': obj_name,
                                     'bbid': bbid
                                    }
                var_places[place]['updown'] = (lnum, place, up, down)
#            if 'indent' not in var_places[place]:
#                var_places[place]['indent'] = self.get_indent(lnum)
            var_places[place]['indent'] = self.get_indent(lnum)
            var_places[place]['vars'].update(varnames)

        vkeys = sorted(var_places.keys())
        for i in range(len(vkeys)-1):
            if var_places[vkeys[i]] == var_places[vkeys[i+1]]:
                del var_places[vkeys[i]]

        result = copy(self.text)
        for lnum in sorted(var_places.keys(), reverse=True):
            indent = var_places[lnum]['indent']
            bbname = "%s:%r" % (var_places[lnum]['prefix'], var_places[lnum]['bbid'])
            for vname in sorted(var_places[lnum]['vars'], reverse=True):
                result.insert(lnum, '%sif "%s" in locals():\n%s\t_trace_changes("%s", "%s", %s) # %r' % \
                              (indent, vname, indent, bbname, vname, vname,
                               var_places[lnum]['updown'] ))

        return result

    def get_indent(self, lnum):
        _get_line_indent = lambda line: re.match('(\s*)', line)
        _def_line = lambda line: re.search('def |class |for|while|if|elif|else|try|except|finally', line)
        _ret_line = lambda line: re.search('return', line)
        _splitted_line = lambda line: re.search(',(\s*)$', line)

        up = self.line_nums2[lnum]['u']
        down = self.line_nums2[lnum]['d']
        our_line = None
        if not _def_line(self.text[up]):
            our_line = up
        else:
            our_line = down

        m =  _get_line_indent(self.text[our_line])
        return m.group(0)

class MyHtmlFormatter(BaseModuleInfo, HtmlFormatter):
    def __init__(self, *args, **kwargs):
        BaseModuleInfo.__init__(self, kwargs['module'])
        del kwargs['module']
        HtmlFormatter.__init__(self, *args, **kwargs)
        self.curlineno = None



    def format(self, tokensource, outfile):
        """
        Format ``tokensource``, an iterable of ``(tokentype, tokenstring)``
        tuples and write it into ``outfile``.
        """
        self.curlineno = 1
        if self.encoding:
            # wrap the outfile in a StreamWriter
            outfile = codecs.lookup(self.encoding)[3](outfile)
        return self.format_unencoded(tokensource, outfile)

    def _format_lines(self, tokensource):
        """
        Just format the tokens, without any wrapping tags.
        Yield individual lines.
        """
        nocls = self.noclasses
        lsep = self.lineseparator
        # for <span style=""> lookup only
        getcls = self.ttype2class.get
        c2s = self.class2style

        lspan = ''
        line = ''
        myescape = lambda x: x.replace('"', '\'')

        f = open('output','w+')
        f.close()
        
        for ttype, value in tokensource:
            curstates = self.linestates.get(self.curlineno, None)

            dumpfile = getglobal('dumpfile')
            if dumpfile:
                f = open(dumpfile, 'a')
    #            print '%i: %r' % (self.curlineno, curstates)
                f.write('%i: %r\n' % (self.curlineno, curstates))
                f.close()
                
            #if curstates is None:
                #print '%i: %r' % (self.curlineno, curstates)
            if ttype == Token.Text and value == '\n':
                self.curlineno += 1
            if Token.Name in (ttype, ttype.parent) or value == 'self':
                f = open('output', 'a')
                f.write('%i : %s : type = %s, value = %s\n' % (self.curlineno, value, myescape(BaseModuleInfo.get_vartypes(curstates,     value)), myescape(BaseModuleInfo.get_varvalues(curstates, value))))
                f.close()
                addedstyle = 'style="%s" title="%s: %s, val: %s"' % (myvar, value, myescape(BaseModuleInfo.get_vartypes(curstates, value)), myescape(BaseModuleInfo.get_varvalues(curstates, value)))
            elif Token.Literal in (ttype.parent, ttype.parent, ttype.parent.parent) and value not in ('\'', '"'):
#                addedstyle= 'style="%s" title="const \'%s\': TODO"' % \
#                        (myconst, value)
                addedstyle= 'style="%s" title="constant"' % myconst
            else:
                addedstyle = ''
            if nocls:
                cclass = getcls(ttype)
                while cclass is None:
                    ttype = ttype.parent
                    cclass = getcls(ttype)
                cspan = cclass and '<span style="%s" %s>' % \
                        (c2s[cclass][0], addedstyle) or ''
            else:
                cls = self._get_css_class(ttype)
                cspan = cls and '<span class="%s" %s>' % \
                        (cls, addedstyle) or ''
            parts = escape_html(value).split('\n')

            # for all but the last line
            for part in parts[:-1]:
                if line:
                    if lspan != cspan:
                        line += (lspan and '</span>') + cspan + part + \
                                (cspan and '</span>') + lsep
                    else: # both are the same
                        line += part + (lspan and '</span>') + lsep
                    yield 1, line
                    line = ''
                elif part:
                    yield 1, cspan + part + (cspan and '</span>') + lsep
                else:
                    yield 1, lsep
            # for the last line
            if line and parts[-1]:
                if lspan != cspan:
                    line += (lspan and '</span>') + cspan + parts[-1]
                    lspan = cspan
                else:
                    line += parts[-1]
            elif parts[-1]:
                line = cspan + parts[-1]
                lspan = cspan
            # else we neither have to open a new span nor set lspan

        if line:
            yield 1, line + (lspan and '</span>') + lsep



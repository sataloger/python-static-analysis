# -*- coding: utf-8 -*-
import sys
import os
import logging
import time
from optparse import OptionParser

# hack: loading VarTypes, create_empty, etc. in __builtin__
import analyzer.pytypes_run.var_types
import analyzer.pytypes_run.interpr_state
import analyzer.pytypes_run.var_aliases

from analyzer.pytypes_run.base_classes import setglobal
from analyzer.pytypes_run.emulation import ProcessModule
from analyzer.db.manage import *
from analyzer.db.tables import *
from analyzer import settings

setglobal('mydebugDict', {})

mydebugDict['printWarnings'] = True
mydebugDict['printNotImplemented'] = False

mydebugDict['printInstr'] = True
mydebugDict['printInstrStackVars'] = True
mydebugDict['printInstrVarsAfterBlock'] = False

mydebugDict['printCommentsSpecTypes'] = True

mydebugDict['runAll'] = True
mydebugDict['runName'] = 'test.f1'

mydebugDict['useAnotherSearch'] = False # работает ~ в 3.2 раза быстрее -

setglobal('mystats', {})
mystats['codeSize'] = 0
mystats['prCount'] = 0
mystats['varsCount'] = 0
mystats['varsUsefulCount'] = 0
mystats['linesCount'] = 0
mystats['assertsCount'] = 0

setglobal('lge_counter', 0)
setglobal('repr_counter', 0)
setglobal('aliasanalysis', False)

if __name__=="__main__":
    x = time.time()

    # parse parameters
    parser = OptionParser()
    parser.set_usage("%s <-f <filename>>" % (sys.argv[0]))
    parser.add_option("-f", "--file",
        action='store',
        type='string',
        dest='filename',
        default = '',
        help='path to analyzed file')
    parser.add_option("--output",
        action='store',
        type='string',
        dest='output',
        default = 'html',
        help = 'output format for analysis results')
    options, args = parser.parse_args()

    if options.filename=='':
        parser.print_usage()
        print "Try `%s -h` for more information." % sys.argv[0]
        os._exit(1)

    # setup logging
    try:
        getattr(logging,settings.LOGGING)
    except AttributeError:
        print "Error: LOGGING setting has unsupported value. Try one of these: DEBUG, INFO, WARNING, ERROR"
        os._exit(1)

    logging.basicConfig(format ='%(asctime)s %(levelname)s  %(name)s %(message)s')
    log = logging.getLogger('analyzer')
    log.setLevel(getattr(logging,settings.LOGGING))
    logging.getLogger('sqlalchemy').setLevel(getattr(logging,settings.DATABASE_LOGGING))

    # setup db
    connect()
    syncdb()
    session = get_session()

    # insert filename to db
    filename = os.path.abspath(options.filename)
    split_name = os.path.split(filename)
    entry_file = AnalyzedFile(split_name[0], split_name[1])
    session.add(entry_file)
    session.commit()

    try:
        emul = ProcessModule()
        emul.process(filename)
        emul.save_to_file(filename, filename + ".html", 'html')
    except Exception, ex:
#        e = sys.exc_info()[0]
#        print "Error: %s" % ex
        raise

    disconnect()
    log.debug("Running time: %s sec" %str(time.time() - x))
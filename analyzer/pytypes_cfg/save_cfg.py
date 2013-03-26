#!/usr/bin/env python2.5
# -*- coding: utf-8 -*-
import os
import shutil
import sys
import time
import yapgvb
from optparse import OptionParser
from analyzer.pytypes_cfg.cfg_creator import CFGCreator

def save_cfg(module, path, format, all_instructions):
    print 'Saving images(of %i): ' % len(module.cfg),
    i = 1
    for name,graph in module.dot_repr(all_instructions):
        graph.layout(yapgvb.engines.dot)
        filename = path+"/"+str(name) + "." + format
        graph.render(filename)
        sys.stdout.write('%i.' % i)
        sys.stdout.flush()
        i += 1
    print '.. Done.'
        
if __name__ == '__main__':
    parser = OptionParser()
    parser.set_usage("%s [-f <format>] [-o <output_dir>] filename" % (sys.argv[0]))
    parser.add_option("-f", "--format",
        action='store',
        type='string',
        dest='format',
        default = 'png',
        help='one of png, jpg, jpeg, ps, pdf, etc.')
    parser.add_option("-o", "--output_directory",
        action='store',
        type='string',
        dest='dir_name',
        default = '')
    parser.add_option("-a", "--all_instructions",
        action='store_true',
        dest='all_instructions',
        default = False)
    options, args = parser.parse_args()
    
    if len(args) != 1:
        parser.print_usage()
        print "Try `%s -h` for more information." % sys.argv[0]
        sys.exit(0)

    if options.format not in yapgvb.formats:
        print "Unsupported graph output format"
        sys.exit(0)

    if options.dir_name=='':
        base_dir = os.path.dirname(os.path.abspath(args[0]))+"\\cfg_pic\\"
    else:
        base_dir = options.dir_name
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
        time.sleep(1)
    os.mkdir(base_dir)

    save_cfg(CFGCreator.make_cfgs(args[0]), base_dir, options.format, options.all_instructions)

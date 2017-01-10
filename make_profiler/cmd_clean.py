#!/usr/bin/python3

import os
import sys
import logging
import shutil
import argparse

from make_profiler.parser import parse, get_dependencies_influences, Tokens


def rm_node(node):
    if not os.path.exists(node):
        return
    logging.info('removing %s', node)
    if os.path.isdir(node):
        shutil.rmtree(node)
    else:
        os.remove(node)


def clean_target(target, subtree):
    if target not in subtree:
        return
    for subtarget in subtree[target]:
        rm_node(subtarget)
        clean_target(subtarget, subtree)


def main(argv=sys.argv[1:]):
    options = argparse.ArgumentParser(
        description='Removes the target and everything this target leads to.')
    options.add_argument(
        '-f',
        action='store',
        dest='in_filename',
        type=str,
        default='Makefile',
        help='Makefile to read (default %(default)s)')
    options.add_argument(
        'targets',
        default=['all'],
        metavar='target',
        type=str,
        nargs='*',
        help='Targets to process')

    args = options.parse_args(argv)
    in_file = open(args.in_filename, 'r') if args.in_filename else sys.stdin

    ast = parse(in_file)
    deps, influences, order_only, indirect_influences = get_dependencies_influences(ast)

    for target in args.targets:
        rm_node(target)
        clean_target(target, influences)


if __name__ == '__main__':
    main()
